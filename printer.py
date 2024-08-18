import os
import win32print
import win32api

def print_pdf(file_path):
    # デフォルトプリンタを取得
    printer_name = win32print.GetDefaultPrinter()
    
    # 印刷コマンドを実行
    win32api.ShellExecute(
        0,
        "print",
        file_path,
        None,
        ".",
        0
    )

# 印刷したいPDFファイルのパスを指定
pdf_path = r'C:\Users\hirokikawai\OneDrive - OUMail (Osaka University)\freestep\flasktest\uploads\ddc5ea07-f7ff-4dad-ac97-43733c9a3f7e_final_exam.pdf'
print_pdf(pdf_path)
