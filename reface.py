import replicate
import os


def syn(target_img):
    # 사진 합성
    os.environ["REPLICATE_API_TOKEN"] = "REPLICATE_API_TOKEN_VALUE"
    output = replicate.run(
        "lucataco/faceswap:9a4298548422074c3f57258c5d544497314ae4112df80d116f0d2109e843d20d",
        input={
            "swap_image": open("captured_image.jpg", "rb"),
            "target_image": open(target_img, "rb")
        }
    )

    os.system("curl " + output + " > output.jpg")
