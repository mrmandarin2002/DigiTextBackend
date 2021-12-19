## DigiText PDF utils
## Made by FearlessDoggo21

import reportlab
from reportlab.graphics.shapes import String
from reportlab.platypus import \
    SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm, inch
from reportlab.graphics.barcode.code128 import Code128


def textbook_barcodes(lower_bound: int, upper_bound : int, filename="test.pdf"):
    '''
    Creates a PDF containing a 3x10 array of barcodes per page.  
    Each barcode corresponds to an inputtend number, 
    guaranteed to be in order.  
    Uses Code128 barcodes.

    Inputs:  
    `numbers`: a list of barcode numbers that will be 0
    extended to 8 digits  
    `filename`: the output file to be created or overwritten
    '''
    numbers = [num for num in range(lower_bound, upper_bound)]
    catalog = list()
    ## Steps 3 for each row in the table
    for i in range(0, len(numbers) - (len(numbers) % 3), 3):
        catalog.append(Table(
            ## Creates list of 3 barcodes from list section
            [[Code128(
                str(numbers[j]).zfill(8),
                barWidth=0.05 * cm,
                barHeight=1.5 * cm,
                humanReadable=True
            ) for j in range(i, i + 3)]],
            ## Table styling options
            colWidths=[7 * cm],
            rowHeights=[2.55 * cm],
            style=TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP")
            ])
        ))

    if len(numbers) % 3:
        catalog.append(Table(
            [[Code128(
                str(numbers[i]).zfill(8),
                barWidth=0.05 * cm,
                barHeight=1.5 * cm,
                humanReadable=True
            ) for i in range(len(numbers) - (len(numbers) % 3), len(numbers))]],
            colWidths=[7 * cm],
            rowHeights=[2.55 * cm],
            style=TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP")
            ])
        ))

    SimpleDocTemplate(
        "barcode_pdfs/" + filename, 
        pagesize=letter,
        rightMargin=0,
        leftMargin=0,
        topMargin=1.25 * cm,
        bottomMargin=0
    ).build(catalog)


def book_return_page(school_code: str, student_name: str, student_number,
    books: list, filename="test.pdf"):
    '''
    Creates a PDF containing a student's name, number barcode, 
    and returning textbooks.  
    Uses a Code128 barcode.

    Inputs:  
    `student_name`: the name of the student  
    `student_number`: the unique id of the student  
    `books`: a list containing book information in
    the following order:  
        Number, Name: str, Charge, Type (OUT, DAMAGED, etc)
    `filename`: the output file to be created or overwritten
    '''

    canvas = Canvas(filename, letter)
    canvas.setFont("Times-Roman", 28)
    canvas.drawString(inch * 0.5, 10 * inch, student_name)

    Code128(
        str(student_number),
        barWidth=0.05 * cm,
        barHeight=1.5 * cm,
        humanReadable=True
    ).drawOn(canvas, 5.5 * inch, 9.75 * inch)

    height = 9.25 * inch
    canvas.setFont("Times-Roman", 16)
    for book in books:

        title_cutoff = 40
        if book[3] == "DAMAGED":
            title_cutoff = 30

        # makes sure book title isn't too long
        if len(book[1]) > 35:
            book[1] = book[1][:title_cutoff] + '...'

        book_title = book[1] + ' (' + book[3] + ')'

        if book[3] == "DAMAGED":
            book_title += ' ' + book[4][0] + ' > ' + book[4][1]

        canvas.drawString(0.5 * inch, height, str(book[0]))
        canvas.drawString(1.5 * inch, height, book_title)
        canvas.drawString(7.25 * inch, height, "$" + str(book[2]))
        canvas.line(0.5 * inch, height - 0.095 * inch, inch * 8, height - 0.095 * inch)
        height -= 0.30 * inch

    canvas.drawString(6.66 * inch, height - 0.1 * inch, "Total: $" + str(sum([book[2] for book in books])))

    canvas.showPage()
    canvas.save()
