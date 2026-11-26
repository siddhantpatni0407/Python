import pikepdf
import os

def remove_pdf_password():

    print("=" * 50)
    print("         PDF PASSWORD REMOVER")
    print("=" * 50)

    # Ask for PDF path
    input_pdf = input(
        "\nEnter the complete PDF file path: "
    ).strip().strip('"')

    # Check file existence
    if not os.path.isfile(input_pdf):
        print("\nERROR: PDF file not found!")
        input("\nPress Enter to exit...")
        return

    print("\nPDF found successfully!")

    # Ask for password (visible while typing)
    password = input("\nEnter PDF password: ")

    # Generate output path in same folder
    folder_path = os.path.dirname(os.path.abspath(input_pdf))
    file_name = os.path.splitext(os.path.basename(input_pdf))[0]

    output_pdf = os.path.join(
        folder_path,
        file_name + "_unlocked.pdf"
    )

    try:
        print("\nProcessing PDF... Please wait.")

        with pikepdf.open(input_pdf, password=password) as pdf:

            pdf.save(
                output_pdf,
                encryption=False
            )

        print("\n" + "=" * 50)
        print("SUCCESS!")
        print("Password protection removed.")
        print("\nOutput file saved at:")
        print(output_pdf)
        print("=" * 50)

    except pikepdf.PasswordError:
        print("\nERROR: Incorrect PDF password!")

    except Exception as e:
        print("\nERROR:", str(e))

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    remove_pdf_password()
