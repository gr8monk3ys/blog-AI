import numpy as np
import matplotlib.pyplot as plt
from skimage import io, color
from skimage.measure import find_contours
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import base64
from PIL import Image
from io import BytesIO

def generate_logo(company_name):
    logo_template = PromptTemplate(
        input_variables=["company_name"], 
        template="""You are a highly skilled graphic designer with years of experience in creating unique and memorable logos. Your task is to design a logo for the following company.

    Company Name: {company_name}

    The logo should be modern, professional, and visually appealing. It should reflect the company's brand and values, and be suitable for use across various mediums such as websites, business cards, and promotional materials. Consider the company's target audience and industry when designing the logo. The logo should be versatile, scalable, and look good in both color and black-and-white formats. Additionally, it should be simple enough to be easily recognizable, yet unique enough to stand out from competitors.
            """
    )

    llm = OpenAI(model="dalle-3", temperature=0.7)
    logo_chain = LLMChain(
        llm=llm,
        prompt=logo_template,
    )
    logo = logo_chain.run({
        "company_name": company_name
    })
    print(f"Generated Logo: {logo}\n")
    return logo.strip()

def save_logo_image(logo_data, file_path):
    image_data = base64.b64decode(logo_data)
    image = Image.open(BytesIO(image_data))
    image.save(file_path)

def vectorize_image(image_path):
    image = io.imread(image_path)
    grayscale = color.rgb2gray(image)
    contours = find_contours(grayscale, 0.8)

    fig, ax = plt.subplots()
    ax.imshow(grayscale, cmap=plt.cm.gray)

    for contour in contours:
        ax.plot(contour[:, 1], contour[:, 0], linewidth=2)

    ax.set_xticks([])
    ax.set_yticks([])
    plt.show()

    return contours

company_name = input('Your Company Name: ')
logo = generate_logo(company_name)
logo_image_path = 'generated_logo.png'
save_logo_image(logo, logo_image_path)
vectorize_image(logo_image_path)