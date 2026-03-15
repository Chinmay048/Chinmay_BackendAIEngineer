# Create a minimal valid PDF
pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
100 700 Td
(Mathematics Fundamentals) Tj
0 -30 Td
(Chapter 1: Numbers and Basic Operations) Tj
0 -30 Td
(Numbers are the foundation of mathematics. Addition is one of the most basic operations.) Tj
0 -20 Td
(When we add two numbers, we combine their values. For example, 2 plus 3 equals 5.) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000262 00000 n
0000000515 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
609
%%EOF
"""

with open('sample_pdf_grade3_math_fundamentals.pdf', 'wb') as f:
    f.write(pdf_content)
print('✓ PDF created: sample_pdf_grade3_math_fundamentals.pdf')
