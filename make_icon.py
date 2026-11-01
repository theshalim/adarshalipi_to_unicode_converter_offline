"""Builds icon.ico and icon.png (needs Pillow and Nikosh.ttf next to this file)."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

NIKOSH = "Nikosh.ttf"
SEGOE_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
SYMBOL = r"C:\Windows\Fonts\seguisym.ttf"
TOP, BOTTOM = (0x34, 0x49, 0x5E), (0x2C, 0x3E, 0x50)   # palette slate blues


def tile(size, shadow=True):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    m = int(size * .06)
    if shadow:
        sh = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((m, m + size * .02, size - m, size - m + size * .02),
                                             int(size * .23), fill=(0, 0, 0, 80))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size * .025)))
    grad = Image.new("RGBA", (size, size))
    for y in range(size):
        t = y / size
        grad.paste(tuple(int(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3)) + (255,),
                   (0, y, size, y + 1))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((m, m, size - m, size - m), int(size * .23), fill=255)
    im.paste(grad, (0, 0), mask)
    return im


def full(size=1024):
    im = tile(size)
    d = ImageDraw.Draw(im)
    d.text((size * .335, size * .47), "অ", font=ImageFont.truetype(NIKOSH, int(size * .46)),
           fill="white", anchor="mm")
    d.text((size * .70, size * .50), "A", font=ImageFont.truetype(SEGOE_BOLD, int(size * .30)),
           fill=(0xEC, 0xF0, 0xF1), anchor="mm")
    d.text((size * .50, size * .78), "⇄", font=ImageFont.truetype(SYMBOL, int(size * .17)),
           fill=(0xBD, 0xC3, 0xC7), anchor="mm")
    return im


def small(size):
    im = tile(256, shadow=False)
    ImageDraw.Draw(im).text((128, 116), "অ", font=ImageFont.truetype(NIKOSH, 235),
                            fill="white", anchor="mm")
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    master = full()
    sizes = (16, 20, 24, 32, 40, 48, 64, 128, 256)
    frames = [small(n) if n <= 32 else master.resize((n, n), Image.LANCZOS) for n in sizes]
    frames[-1].save("icon.ico", format="ICO", sizes=[(n, n) for n in sizes], append_images=frames[:-1])
    master.resize((256, 256), Image.LANCZOS).save("icon.png")
    print("icon.ico, icon.png written")
