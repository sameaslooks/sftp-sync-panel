"""Generate assets/icon.ico — run once from the project root."""
import io, os, struct
from PIL import Image, ImageDraw

BLUE  = (37, 99, 235, 255)
WHITE = (255, 255, 255, 245)


def _render(size: int) -> Image.Image:
    ss = 4
    S  = size * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    r = S // 5
    d.rounded_rectangle([(0, 0), (S - 1, S - 1)], radius=r, fill=BLUE)

    aw  = S * 36 // 100
    ah  = S * 52 // 100
    hh  = S * 22 // 100
    sw  = S * 16 // 100
    gap = S * 10 // 100
    pad = S * 14 // 100

    total_w = aw * 2 + gap
    start_x = (S - total_w) // 2
    lx, rx  = start_x, start_x + aw + gap

    def up_arrow(x, y):
        cx = x + aw // 2
        sx = x + (aw - sw) // 2
        d.polygon([(cx, y), (x, y + hh), (x + aw, y + hh)], fill=WHITE)
        d.rectangle([sx, y + hh, sx + sw - 1, y + ah - 1], fill=WHITE)

    def down_arrow(x, y):
        by = y + ah - 1
        cx = x + aw // 2
        sx = x + (aw - sw) // 2
        d.rectangle([sx, y, sx + sw - 1, by - hh], fill=WHITE)
        d.polygon([(x, by - hh), (x + aw, by - hh), (cx, by)], fill=WHITE)

    up_arrow(lx, pad)
    down_arrow(rx, S - pad - ah)

    return img.resize((size, size), Image.LANCZOS)


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def build_ico(sizes: list[int]) -> bytes:
    """Build a Windows ICO with PNG entries (Vista+ compatible)."""
    images   = [_render(s) for s in sizes]
    png_data = [_png_bytes(img) for img in images]

    n = len(sizes)
    # Header: ICONDIR  (6 bytes) + n * ICONDIRENTRY (16 bytes each)
    header_size = 6 + n * 16
    offsets = []
    off = header_size
    for data in png_data:
        offsets.append(off)
        off += len(data)

    out = io.BytesIO()
    # ICONDIR
    out.write(struct.pack("<HHH", 0, 1, n))
    # ICONDIRENTRYs
    for i, s in enumerate(sizes):
        w = h = s if s < 256 else 0   # 0 means 256 in ICO spec
        out.write(struct.pack(
            "<BBBBHHII",
            w, h,         # width, height (0 = 256)
            0,            # color count (0 = not a palette image)
            0,            # reserved
            1,            # planes
            32,           # bit count
            len(png_data[i]),
            offsets[i],
        ))
    for data in png_data:
        out.write(data)
    return out.getvalue()


if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)

    sizes = [256, 128, 64, 48, 40, 32, 24, 20, 16]
    ico   = build_ico(sizes)

    with open("assets/icon.ico", "wb") as f:
        f.write(ico)

    # also save a reference PNG
    _render(256).save("assets/icon.png")

    print(f"assets/icon.ico  ({len(sizes)} sizes, PNG entries)")
    print("assets/icon.png  (256 px)")
