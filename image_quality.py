"""Basic image quality screening (resolution, blur, exposure). Not liveness or OCR."""
import io
import numpy as np
from PIL import Image, ImageOps

def analyze(data: bytes, min_side=600, blur_min=60.0):
    """Return dict(ok, issues, metrics). Blur = variance of a Laplacian filter."""
    issues = []
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert('L')
    except Exception:
        return {'ok': False, 'issues': ['File is not a readable image.'], 'metrics': {}}
    w, h = img.size
    a = np.asarray(img, dtype=np.float32)
    lap = (-4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:])
    blur, bright = float(lap.var()), float(a.mean())
    if min(w, h) < min_side: issues.append(f'Low resolution ({w}×{h}); retake closer/in better light.')
    if blur < blur_min: issues.append('Image looks blurry; hold the camera steady.')
    if bright < 55: issues.append('Too dark; move to better light.')
    if bright > 215: issues.append('Overexposed/glare; avoid direct light.')
    return {'ok': not issues, 'issues': issues,
            'metrics': {'width': w, 'height': h, 'sharpness': round(blur, 1), 'brightness': round(bright, 1)}}
