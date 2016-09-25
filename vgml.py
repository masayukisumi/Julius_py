#!/usr/bin/python
# -*- coding: utf-8 -*-
# python test1.py /home/pi/Desktop/

import subprocess
import sys
import smtplib
import email
import traceback
import socket
import cStringIO

from xml.etree.ElementTree import fromstring
from email import Encoders
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText

# メールアカウント 
MAIL_ADDRESS = "自身のメールアドレスを入力"
MAIL_PASSWARD = "パスワードを入力"
TO_MAIL_ADDRESS = "宛先メールアドレスを入力"

# SMTPサーバ設定
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Juliusサーバ
JULIUS_HOST = "192.168.100.103"
JULIUS_PORT = 10500


# メールメッセージを作成
def create_message(from_addr, to_addr, subject, body, mime=None, attach_file=None):
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Date"] = email.utils.formatdate()
    msg["Subject"] = Header(subject)
    body = MIMEText(body)
    msg.attach(body)
 

    # 添付ファイル
    if mime != None and attach_file != None:
        attachment = MIMEBase(mime['type'],mime['subtype'])
        file = open(attach_file['path'])
        attachment.set_payload(file.read())
        file.close()
        Encoders.encode_base64(attachment)
        msg.attach(attachment)
        attachment.add_header("Content-Disposition","attachment", filename=attach_file['name'])
 
    return msg


# メールを送信する
def send_email(smtp_server, smtp_port, from_mail_address, from_mail_passward, to_mail_address, subject, body, attach_file):
    # メッセージの作成
   
    
   #msg = create_message(from_mail_address, to_mail_address, subject, body, mime, attach_file)
    # 送信
    smtpobj = smtplib.SMTP(smtp_server, smtp_port)
    smtpobj.ehlo()
    # gmailを使うのでTLSを用いる
    smtpobj.starttls()
    smtpobj.ehlo()
    smtpobj.login(from_mail_address, from_mail_passward)
    smtpobj.sendmail(from_mail_address, [to_mail_address], msg.as_string())
    smtpobj.close()


# juliusの解析結果のXMLをパース
def parse_recogout(xml_data):
    # scoreを取得(どれだけ入力音声が、認識結果と合致しているか)
    shypo = xml_data.find(".//SHYPO")
    if shypo is not None:
        score = shypo.get("SCORE")

    # 認識結果の単語を取得
    whypo = xml_data.find(".//WHYPO")
    if whypo is not None:
        word = whypo.get("WORD")
    return score, word

# fswebcamで写真を撮る
def take_picuture(picutre_dir):
    file_name = datetime.now().strftime('%Y%m%d_%H%M%S') + ".jpg"
    file_path = picture_dir + file_name
    cam_command = "fswebcam -r 640x480 {0} -F 10".format(file_path)
    p_camera = subprocess.Popen(cam_command,  shell=True)

    # 写真撮影完了までwaitする
    p_camera.wait()

    return file_name, file_path

if __name__ == "__main__":
    # 写真の保存先ディレクトリ
    picture_dir = sys.argv[1]
    if not picture_dir.endswith("/"):
        picture_dir += "/"

    try:
        # TCP/IPでjuliusに接続
        bufsize = 4096
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((JULIUS_HOST, JULIUS_PORT))
        sock_file = sock.makefile()

        xml_buff = ""
        in_recogout = False

        while True:
            # juliusから解析結果を取得
            data = cStringIO.StringIO(sock.recv(bufsize))

            # 解析結果から一行取得
            line = data.readline()

            while line:
                # 音声の解析結果を示す行だけ取り出して処理する。
                # RECOGOUTタグのみを抽出して処理する。
                if line.startswith("<RECOGOUT>"):
                    in_recogout = True
                    xml_buff += line
                elif line.startswith("</RECOGOUT>"):
                    xml_buff += line
                    xml_data = fromstring(xml_buff)
                    # XMLをパースして、解析結果を取得する
                    score, word = parse_recogout(xml_data)

                    if u'ここにキーワードを入力する' in word:
                        # キーワードが呼ばれたら写真を撮る
                        file_name, file_path = take_picuture(picture_dir)

                        # 添付ファイルの情報を作成
                        
                        mime = {'type':'image','subtype':'jpg'}
                        attach_file={'name':file_name,'path':file_path}
                        #attach_file={'name':'test.jpg','path':'/home/pi/Desktop/test.jpg'}
                        msg = create_message(MAIL_ADDRESS,TO_MAIL_ADDRESS, "Images", "Images", mime, attach_file)
                     
                        # メール送信
                        send_email(SMTP_SERVER, SMTP_PORT, MAIL_ADDRESS, MAIL_PASSWARD, TO_MAIL_ADDRESS, "papa called", "papa called",attach_file)

                    in_recogout = False
                    xml_buff = ""
                else:
                    if in_recogout:
                        xml_buff += line
                # 解析結果から一行取得
                line = data.readline()
    except Exception as e:
        print "error occurred", e, traceback.format_exc()
    finally:
        pass
