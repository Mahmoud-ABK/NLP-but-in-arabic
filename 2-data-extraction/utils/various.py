from IPython.display import HTML, display

def arabic_print(*args):
    for arg in args:
        display(HTML(f"""
        <div dir="rtl" style="text-align: right; font-size: 16px;">
        {str(arg)}
        </div>
        """))
