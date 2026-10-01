from flask import Flask, render_template, request, send_file, jsonify
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
import io

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def cartoonize(image_rgb: np.ndarray) -> np.ndarray:
    """Apply a clean cartoon treatment while preserving natural image colors."""
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

    # Smooth color regions without destroying important boundaries.
    color = cv2.bilateralFilter(image_bgr, d=9, sigmaColor=180, sigmaSpace=180)

    # Build stable dark outlines from an adaptive-threshold edge mask.
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        blockSize=9,
        C=7,
    )

    cartoon_bgr = cv2.bitwise_and(color, color, mask=edges)
    return cv2.cvtColor(cartoon_bgr, cv2.COLOR_BGR2RGB)


def prepare_image(file_storage) -> np.ndarray:
    image = Image.open(file_storage)
    if image.format not in ALLOWED_FORMATS:
        raise ValueError("Unsupported image format")

    # Normalise orientation/mode and constrain huge uploads for responsive processing.
    image = image.convert("RGB")
    image.thumbnail((2200, 2200))
    return np.asarray(image)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if "file" not in request.files:
        return jsonify({"error": "No image was uploaded."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "Please choose an image first."}), 400

    try:
        image = prepare_image(file)
        cartoon_img = cartoonize(image)

        output = Image.fromarray(cartoon_img)
        image_io = io.BytesIO()
        output.save(image_io, "JPEG", quality=94, optimize=True)
        image_io.seek(0)

        return send_file(
            image_io,
            mimetype="image/jpeg",
            download_name="avatarforge-cartoon.jpg",
        )
    except (UnidentifiedImageError, ValueError):
        return jsonify({"error": "Please upload a valid JPG, PNG, or WEBP image."}), 400
    except Exception:
        app.logger.exception("Avatar generation failed")
        return jsonify({"error": "We could not process that image. Please try another one."}), 500


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "Image is too large. Maximum upload size is 10 MB."}), 413


if __name__ == "__main__":
    app.run(debug=True)
