
import qrcode
import os
import uuid


def generate_qr_code(attendance_url):
    os.makedirs("static/qr_codes", exist_ok=True)

    filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join("static", "qr_codes", filename)

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(attendance_url)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    image.save(filepath)

    # Return a web-friendly path
    return f"qr_codes/{filename}"
