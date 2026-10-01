STYLE_HINTS={"cartoon":"clean premium cartoon portrait","sketch":"detailed pencil sketch portrait","comic":"bold comic-book ink portrait","portrait":"soft professional editorial portrait","grayscale":"dramatic monochrome portrait","edgepop":"vivid graphic portrait"}

def build_prompt(user_prompt: str|None, style: str, intensity: int)->str:
    base=(user_prompt or "").strip()
    hint=STYLE_HINTS.get(style,"stylized portrait")
    return f"Preserve the subject's identity and facial structure. Create a {hint}. Style strength {intensity}%. {base}".strip()
