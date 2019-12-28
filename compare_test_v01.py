import os
import shutil
from datetime import datetime
start_time = datetime.now()
from header_extracr_v01 import Header_module_list_all
from header_extracr_v01 import Header_module_base
from header_extracr_v01 import Header_register_list
from header_extracr_v01 import input_Header_name
from temporary_8MN import module_list_all
from temporary_8MN import register_list
from temporary_8MN import module_base
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64
from email.header import Header

folder_name=input_Header_name+'_error'
if os.path.isdir(folder_name):
    ss = os.getcwd() + '/' + folder_name
    shutil.rmtree(ss)
os.mkdir(folder_name)
ss = os.getcwd() + '/' + folder_name
test_error = ss + '/' + 'Error.txt'
test_error_list = ss + '/' + input_Header_name + '_Error_list.yml'
fp=open(test_error,'a')

# check module base address
def find_base_Error():
    fp.write('Error of Module base address：')
    List_Module_Header=list(Header_module_base.keys())  # extract the information of the first column
    List_Module_RM=list(module_base.keys())
    Redundant_List_Module_header = set(List_Module_Header).difference(List_Module_RM)
    Redundant_List_Module_RM = set(List_Module_RM).difference(List_Module_Header)
    if len(Redundant_List_Module_header)>0:  # find the redundant module of Header_file and RM
        if 'I2S' in Redundant_List_Module_header and 'SAI' in Redundant_List_Module_RM:
           Redundant_List_Module_header.remove('I2S')
        if len(Redundant_List_Module_header)>0:
            fp.write('\n  Error1: Header has redundant module: %s' % Redundant_List_Module_header)
    if len(Redundant_List_Module_RM) > 0:
        if 'I2S' in Redundant_List_Module_header and 'SAI' in Redundant_List_Module_RM:
           Redundant_List_Module_header.remove('SAI')
        if len(Redundant_List_Module_header)>0:
            fp.write('\n  Error2: RM has redundant module: %s' % Redundant_List_Module_RM)
    Common_module = set(List_Module_Header).difference(Redundant_List_Module_header)  # find the same module to compare
    for d in range(len(Header_module_base)):
        Module_base_Header=Header_module_base.get(List_Module_Header[d])
        if Module_base_Header in Common_module:
                Module_base_RM = module_base.get(List_Module_Header[d])
                if Module_base_Header == Module_base_RM:
                    pass
                else:
                    fp.write('\n  Error3: Mismatch %s module base address RM: %s Header: %s ' % (List_Module_Header[d],Module_base_RM,Module_base_Header))
# check module register
def find_module_list_all_error():
    fp.write('\n \nError of Module Register list')
    Module_H = list(Header_module_list_all.keys())  # extract key value(module) list
    Module_R = list(module_list_all.keys())
    Redundant_Module_H = set(Module_H).difference(Module_R)
    Redundant_Module_R = set(Module_R).difference(Module_H)
    if len(Redundant_Module_H)>0:
        fp.write('\n  Error4: Header has redundant module: %s' % Redundant_Module_H)
    if len(Redundant_Module_R)>0:
        fp.write('\n  Error5: RM has redundant module: %s' % Redundant_Module_R)
    Common_module_all = set(Module_H).difference(Redundant_Module_H)
    for g in range(len(Header_module_list_all)):
        if Module_H[g] in Common_module_all:
            fp.write('\n  In Module %s' % Module_H[g])
            H_data = Header_module_list_all.get(Module_H[g])
            R_data =module_list_all.get(Module_H[g])  # get the same module to compare with from two dicts
            Register_H = list(H_data.loc[:, 'Name'])
            Register_R = list(R_data.loc[:, 'Name'])
            Redundant_register_data = set(Register_H).difference(set(Register_R))
            Redundant_register_RM = set(Register_R).difference(set(Register_H))
            if len(Redundant_register_data) > 0:  # print the redundant module of Header_file and RM
                fp.write('\n    Error6: Header has redundant register: %s' % Redundant_register_data)
            if len(Redundant_register_RM) > 0:
                print( )
                fp.write('\n    Error7: RM has redundant register: %s' % Redundant_register_RM)
            common_offset = list(set(Register_H).difference(set(Redundant_register_data)))
            for h in range(len(H_data)):
                name_H=H_data.iat[h,1]
                if name_H in common_offset:
                    for i in range(len(R_data)):
                        name_R=R_data.iat[i,1]
                        if name_H ==name_R:
                            if R_data.iat[i,0] in H_data.iat[h,0].split('|'):
                                if H_data.iat[h,2]==R_data.iat[i,2]:
                                    if R_data.iat[i,3] in H_data.iat[h,3].split('|'):
                                        pass
                                    else:
                                        Access=R_data.iat[i,3].replace('\r',' ')  # 去掉换行((reads 0)的情况
                                        fp.write('\n    Error8: Mismatch Access of register: %s Header : %s | RM : %s' % (H_data.iat[h,1],H_data.iat[h,3],Access))
                                else:
                                    fp.write('\n    Error9: Mismatch Width of register: %s Header: %s  | RM: %s ' % (H_data.iat[h,1],H_data.iat[h,2],R_data.iat[i,2]))
                                    if R_data.iat[i,3] in H_data.iat[h,3].split('|'):
                                        pass
                                    else:
                                        fp.write('\n    Error10: Mismatch Access of register: %s Header : %s | RM : %s ' % (H_data.iat[h,1],H_data.iat[h,3],R_data.iat[i,3]))
                            else:
                                fp.write('\n    Error11: Mismatch offset of register: %s Header: %s  | RM: %s ' % (H_data.iat[h,1],H_data.iat[h,0],R_data.iat[i,0]))
                                if H_data.iat[h,2]==R_data.iat[i,2]:
                                    if R_data.iat[i,3] in H_data.iat[h,3].split('|'):
                                        print(H_data.iat[h,3])
                                        pass
                                    else:
                                        fp.write('\n    Error12: Mismatch Access of register: %s  Header : %s | RM : %s ' % (H_data.iat[h,1],H_data.iat[h,3],R_data.iat[i,3]))
                                else:
                                    fp.write('\n    Error13: Mismatch Width of register: %s Header: %s |RM: %s ' % (H_data.iat[h,1],H_data.iat[h,2],R_data.iat[i,2]))
                                    if R_data.iat[i,3] in H_data.iat[h,3].split('|'):
                                        pass
                                    else:
                                        fp.write('\n    Error14: Mismatch Access of register: %s Header : %s |RM : %s ' % (H_data.iat[h,1],H_data.iat[h,3],R_data.iat[i,3]))


# check bit information
def find_Register_Error():
    fp.write('\n\nError of Module Register bit')
    Module_data = list(Header_register_list.keys())  # extract key value(module) list
    Module_RM = list(register_list.keys())
    Redundant_Module_H = set(Module_data).difference(Module_RM)
    Redundant_Module_R = set(Module_RM).difference(Module_data)
    if len(Redundant_Module_H)>0:
        fp.write('\n  Error15: Header has redundant module: %s' % Redundant_Module_H)
    if len(Redundant_Module_R)>0:
        fp.write('\n  Error16: RM has redundant module: %s' % Redundant_Module_R)
    Common_module = set(Module_data).difference(Redundant_Module_H)

    for a in range(len(Module_data)):
        if Module_data[a] in Common_module:
            fp.write('\n  In Module %s' % Module_data[a])
            Header_file_data = Header_register_list.get(Module_data[a])
            RM_data = register_list.get(Module_data[a]) # get the same module to compare with from two dicts
            Register_data=list(Header_file_data.loc[:,'name'])
            Register_RM=list(RM_data.loc[:,'name'])
            Redundant_register_data = list(set(Register_data).difference(set(Register_RM)))
            Redundant_register_RM = list(set(Register_RM).difference(set(Register_data)))
            if len(Redundant_register_data)>0:  # 如果存在多余寄存器则输出
                fp.write('\n    Error17: Header has redundant register: %s' % Redundant_register_data)
            if len(Redundant_register_RM)>0:
                fp.write('\n    Error18: RM has redundant register: %s' %  Redundant_register_RM)
            common_register = list(set(Register_data).difference(set(Redundant_register_data)))

            for n in range(len(Header_file_data)):
                Register_data = Header_file_data.iat[n, 0]
                if Register_data in common_register:
                    for m in range(len(RM_data)):
                        Register_RM = RM_data.iat[m, 0]
                        if Register_data == Register_RM:
                            if Header_file_data.iat[n, 1].keys() == RM_data.iat[m, 1].keys():
                                if Header_file_data.iat[n, 1].items() == RM_data.iat[m, 1].items():
                                    pass
                                else:
                                    fp.write(
                                        '\n    Error19: Mismatch bit field in Module:%s in Register : %s Header_file_data information:%s in line : %s |RM_data information:%s  in page : %s' % (
                                            Module_data[a], Register_data,
                                            Header_file_data.iat[n, 1].items() - RM_data.iat[m, 1].items(),
                                            Header_file_data.iat[n, 2],
                                            RM_data.iat[m, 1].items() - Header_file_data.iat[n, 1].items(),
                                            RM_data.iat[n, 2]))  # print bit_mask don't match
                            else:
                                Header_file_data_bit_list = list(Header_file_data.iat[n, 1].keys())  # print bit_name don't match
                                RM_data_bit_list = list(RM_data.iat[m, 1].keys())
                                Redundant_bit_data = list(
                                    set(Header_file_data_bit_list).difference(set(RM_data_bit_list)))
                                Redundant_bit_RM = list(
                                    set(RM_data_bit_list).difference(set(Header_file_data_bit_list)))
                                if len(Redundant_bit_data) > 0:
                                    for L in range(len(Redundant_bit_data)):
                                        if '-0' in Redundant_bit_data[L-1]:  # remove error of bit 0,will check from next
                                            Redundant_bit_data.remove(Redundant_bit_data[L-1])
                                    if len(Redundant_bit_data)>0:
                                        fp.write(
                                        '\n    Error20: Header has redundant bit: %s in register : %s ' % (
                                        Redundant_bit_data, Register_data))
                                if len(Redundant_bit_RM)>0:
                                    Miss_bit = []
                                    for kk in range(len(Redundant_bit_RM)):
                                        Add_bit=Redundant_bit_RM[kk]
                                        Add_bit_name=RM_data.iat[m, 1].get(str(Add_bit))
                                        if 'miss bit field' in Add_bit:  # remove bit 0 situation
                                            for cc in range(len(Header_file_data_bit_list)):
                                                Bit_start=Header_file_data_bit_list[cc]
                                                if '-0' in Bit_start:
                                                    Bit_start_name=Header_file_data.iat[n, 1].get(Bit_start)
                                                    if Add_bit_name == Bit_start_name:
                                                        Miss_bit.append(Add_bit)
                                                    else:
                                                        Miss_bit.append(Add_bit)
                                                        print(fp.write(
                                                        '\n    Error21: Mismatch bit name in register: %s Header: %s | RM: %s ' % (
                                                            Register_data,Bit_start_name, Add_bit_name)))
                                        if 'Reserved' in Add_bit_name:  # remove reserve situation
                                            Miss_bit.append(Add_bit)
                                            # for dd in range(len(Header_file_data_bit_list)):
                                            #     Bit_start = Header_file_data_bit_list[dd]
                                            #     Bit_start_name = Header_file_data.iat[n, 1].get(Bit_start)
                                            #     if Bit_start== Add_bit:
                                            #         if Add_bit_name == Bit_start_name:
                                            #             print(Add_bit_name)
                                            #             Miss_bit.append(Add_bit)
                                            #         else:
                                            #             Miss_bit.append(Add_bit)
                                            #             print(fp.write(
                                            #             '\n    Error21: Mismatch bit name in register: %s Header: %s | RM: %s ' % (
                                            #                 Register_data,Bit_start_name, Add_bit_name)))

                                        if Add_bit_name =='-':
                                            Miss_bit.append(Add_bit)
                                    New_Redundant_bit_RM=set(Redundant_bit_RM).difference(set(Miss_bit))

                                    if len(New_Redundant_bit_RM)>0:
                                        fp.write(
                                        '\n    Error22: RM has redundant bit: %s in register : %s ' % (
                                            New_Redundant_bit_RM, Register_data))

                                common_bit_list = list(set(Header_file_data_bit_list).difference(Redundant_bit_data))
                                for i in range(len(Header_file_data_bit_list)):
                                    if Header_file_data_bit_list[i] in common_bit_list:
                                        for k in range(len(RM_data_bit_list)):
                                            if Header_file_data_bit_list[i] == RM_data_bit_list[k]:
                                                Mask_data = (
                                                    Header_file_data.iat[n, 1].get(Header_file_data_bit_list[i]))
                                                Mask_RM = (RM_data.iat[m, 1].get(RM_data_bit_list[k]))
                                                if Mask_data == Mask_RM:
                                                    pass
                                                else:

                                                    fp.write(
                                                        '\n    Error23: Mismatch bit name Header: %s | RM: %s in register: %s' % (
                                                             Mask_data, Mask_RM,Register_data))

#main
find_base_Error()
find_module_list_all_error()
find_Register_Error()
fp.close()
fp=open(test_error,'r')
fo=fp.readlines()
fc=open(test_error_list,'w')
Error_list=[]
for n in range(len(fo)-1):
    if 'In Module' in fo[n]:
        if 'In Module' in fo[n+1]:
            fo[n]=''
    Error_list.append(fo[n])
for i in range(len(Error_list)):
    if 'In Module' in Error_list[i]:
        Error_list[i]= '\n' + Error_list[i]
for e in Error_list:
    fc.write(e)
fc.write(fo[len(fo)-1])
fc.close()

# # 自动发送邮件 设置smtplib所需的参数
# smtpserver = 'smtp-mail.outlook.com'
# smtp_port= 587
# username = 'jie.zhao_1@nxp.com'
# password = 'Candice@1998'
# sender = 'jie.zhao_1@nxp.com'
# receiver = ['jie.zhao_1@nxp.com']
#
# # 构造邮件对象MIMEMultipart对象
# # 下面的主题，发件人，收件人，日期是显示在邮件页面上的。
# msg = MIMEMultipart()
# msg['Subject'] =Header(u'Header file test is done')
# msg['From'] = 'Cammie <jie.zhao_1@nxp.com>'
# # 收件人为多个收件人,通过join将列表转换为以;为间隔的字符串
# msg['To'] = ";".join(receiver)
# # msg['Date']='2012-3-16'
#
# # 构造文字内容
# msg.attach( MIMEText('hello,the auto script of header file is done ,please check the test result!', 'plain', 'utf-8'))
#
# # 构造附件
# with open('/opt/test/Error.yml','rb') as f:
#     # 设置附件的MIME和文件名
#     mime = MIMEBase('yml', 'yml', filename='test.yml')
#     # 加上必要的头信息
#     mime.add_header('Content-Disposition', 'attachment', filename='test.yml')
#     mime.add_header('Content-ID', '<0>')
#     mime.add_header('X-Attachment-Id', '0')
#     # 把附件的内容读出来
#     mime.set_payload(f.read())
#     # 用Base64编码
#     encode_base64(mime)
#     # 添加到MIMEMultipart
#     msg.attach(mime)
#
# # 发送邮件
# smtp = smtplib.SMTP(smtpserver,smtp_port)
# # 我们用set_debuglevel(1)就可以打印出和SMTP服务器交互的所有信息。
# # smtp.set_debuglevel(1)
# smtp.starttls()
# # 创建安全连接来加密
# smtp.login(username, password)
# smtp.sendmail(sender, receiver, msg.as_string())
# smtp.quit()
# end_time = datetime.now()
# print("start time: ", start_time)
# print("end time: ", end_time)
# print("elapsed time: ", end_time - start_time)
