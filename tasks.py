from RPA.HTTP import HTTP
from robocorp.tasks import task
from robocorp import browser
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
from RPA.Assistant import Assistant
import time


ROBOT_ORDER_URL = "https://robotsparebinindustries.com/#/robot-order"
ORDERS_CSV_URL = "https://robotsparebinindustries.com/orders.csv"
OUTPUT_DIR = "output"
RECEIPTS_DIR = f"{OUTPUT_DIR}/receipts"


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(slowmo=100)

    user_input_task()

    orders = get_orders()

    for order in orders:
        close_modal()
        fill_the_form(order)
        preview_robot()

        success = submit_order()
        if not success:
            print(f"Failed to submit order {order['Order number']} after 5 attempts")
            continue

        pdf_path = store_receipt_as_pdf(order["Order number"])
        screenshot_path = screenshot_robot(order["Order number"])
        embed_screenshot_to_receipt(screenshot_path, pdf_path)

        go_to_order_another_robot()

    zip_receipts()


def open_robot_order_website(url):
    browser.goto(url)


def close_modal():
    page = browser.page()
    page.click("button:text('OK')")


def get_orders():
    http = HTTP()
    http.download(ORDERS_CSV_URL, overwrite=True, target_file="orders.csv")
    tables = Tables()
    orders = tables.read_table_from_csv("orders.csv")
    return orders


def fill_the_form(order):
    page = browser.page()

    page.select_option("#head", str(order["Head"]))
    page.click(f"#id-body-{order['Body']}")
    page.fill("input[placeholder='Enter the part number for the legs']", str(order["Legs"]))
    page.fill("#address", order["Address"])


def preview_robot():
    page = browser.page()
    page.click("#preview")


def submit_order():
    page = browser.page()

    max_retries = 5

    for _ in range(max_retries):
        page.click("#order")
        time.sleep(0.5)

        error = page.query_selector(".alert-danger")
        if not error:
            return True

    return False


def store_receipt_as_pdf(order_number):
    page = browser.page()

    receipt_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdf_path = f"{RECEIPTS_DIR}/receipt_{order_number}.pdf"
    pdf.html_to_pdf(receipt_html, pdf_path)

    return pdf_path


def screenshot_robot(order_number):
    page = browser.page()

    screenshot_path = f"{RECEIPTS_DIR}/robot_{order_number}.png"
    page.locator("#robot-preview-image").screenshot(path=screenshot_path)

    return screenshot_path


def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()
    pdf.add_files_to_pdf(
        files=[screenshot],
        target_document=pdf_file,
        append=True
    )


def go_to_order_another_robot():
    page = browser.page()
    page.click("#order-another")


def zip_receipts():
    archive = Archive()
    archive.archive_folder_with_zip(RECEIPTS_DIR, f"{OUTPUT_DIR}/receipts.zip")


def user_input_task():
    assistant = Assistant()
    assistant.add_heading("Input from user")
    assistant.add_text_input("text_input", placeholder="Please enter URL")
    assistant.add_submit_buttons("Submit", default="Submit")
    result = assistant.run_dialog()
    url = result.text_input
    open_robot_order_website(url)
