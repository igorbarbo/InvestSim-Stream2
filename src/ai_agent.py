import google.generativeai as genai

def ask_ai(prompt, df):
    try:
        genai.configure(api_key="AIzaSyAXfzbC-9RGpQgafSG-86AMGK-2AgtOQCU")
        model = genai.GenerativeModel('gemini-1.5-flash')
        ctx = df.to_string()
        res = model.generate_content(f"Carteira Igor: {ctx}\nPergunta: {prompt}")
        return res.text
    except:
        return "IA offline no momento."
      
