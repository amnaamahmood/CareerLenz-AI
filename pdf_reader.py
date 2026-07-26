import logging

from pypdf import PdfReader



# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "CareerLens-PDF"
)





# =====================================================
# PDF TEXT EXTRACTION
# =====================================================


def extract_text_from_pdf(
    uploaded_file
):


    if uploaded_file is None:

        raise ValueError(
            "No PDF file provided."
        )



    try:


        reader = PdfReader(
            uploaded_file
        )



        extracted_text = []



        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):


            try:


                page_text = page.extract_text()



                if page_text:


                    extracted_text.append(
                        page_text
                    )



            except Exception as e:


                logger.warning(

                    f"Failed extracting page {page_number}: {e}"

                )





        final_text = "\n\n".join(
            extracted_text
        ).strip()



        if not final_text:


            raise ValueError(

                "No readable text found in PDF. "
                "The file may be scanned or image-based."

            )



        return final_text





    except Exception as e:


        logger.error(

            f"PDF extraction failed: {e}"

        )


        raise Exception(

            f"Unable to extract PDF text: {str(e)}"

        )