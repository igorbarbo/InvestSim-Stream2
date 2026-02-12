from fpdf import FPDF

class PrivatePDF(FPDF):
    def header(self):
        self.set_fill_color(10, 20, 35) 
        self.rect(0, 0, 210, 45, 'F')
        self.set_font('Times', 'B', 22)
        self.set_text_color(212, 175, 55)
        self.cell(0, 25, 'IGORBARBO PRIVATE WEALTH', 0, 1, 'C')
        self.ln(10)

def generate(df, total_brl, mwa):
    pdf = PrivatePDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 14)
    pdf.cell(0, 10, f"Patrimonio Consolidado: R$ {total_brl:,.2f}", ln=True)
    pdf.ln(10)
    
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(90, 10, ' ATIVO', 0, 0, 'L', 1)
    pdf.cell(90, 10, 'PATRIMONIO ', 0, 1, 'R', 1)
    
    for _, row in df.iterrows():
        pdf.cell(90, 10, f" {row['ticker']}", border='B')
        pdf.cell(90, 10, f"R$ {row['Patrimônio']:,.2f} ", border='B', ln=1, align='R')
        
    return pdf.output(dest='S').encode('latin-1')
  
