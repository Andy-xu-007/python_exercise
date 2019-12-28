#!/user/bin/env python3
# -*- coding: utf-8 -*-

"""
    need to install java, pandas, numpy,lxml
    __author__ = 'Cammie Zhao'
    __author_email__ = "jie.zhao_1@nxp.com"
https://tabula.technology/
"""

import os
import re
import pandas
import shutil
import sys
# a=sys.argv[1]
# input_Header_name = 'K32L3A60_cm0plus' # a
input_Header_name = input('please input your header file name: ')
Header_name = input_Header_name + '.h'
fp = open(Header_name, 'r')
folder_name=input_Header_name+'_H_test'
if os.path.isdir(folder_name):
    ss = os.getcwd() + '/' + folder_name
    shutil.rmtree(ss)
os.mkdir(folder_name)
ss = os.getcwd() + '/' + folder_name
test_info = ss + '/' + 'H_test_info.txt'
test_module = ss + '/' + 'H_module.html'
test_bit = ss + '/' + 'H_bit.html'
M_N = ss + '/' + 'Module_name_list'
Header_test_info = open(test_info,'a+')
Header_test_module = open(test_module,'a+')
Header_test_bit = open(test_bit,'a+')
M = open(M_N,'a+')
Module_name_list=[];Module_name_len_list=[];Register_list=[];Register_name_list=[];Register_len_list=[];Register_star_list=[];Module_Register_len_list=[]
Bit_name_list=[]; Bit_mask_list=[];Module_star_list=[];Module_Register_num=[];Module_count_register=[];Module_Register_list=[];Module_link_Register_list=[]
add=0
fn=fp.readlines()

# Get a list of modules and scope of lines , get a list of registers
for line in fn:
      if re.match(r'\s{3}--\s(.*)\sRegister.*', line):  # extract the name of every module
          name=re.match(r'\s{3}--\s(.*)\sRegister.*', line)
          Module_name_len_list.append(name[1].count('_')+1)
          Module_name_list.append(name[1])
          Module_star_list.append(fn.index(line))  # find the start line of every module
      if re.match(r'.*@name\s(.*)\s-.*', line):
          Register_name=re.match(r'.*@name\s(.*)\s-.*', line)
          Register_name_list.append(Register_name.group(1))
Module_star_list.append(len(fn))  # add last line, extract the last module

line_list=[]
# get the scope of registers
for num in range(len(Module_star_list)-1):
    for n in range(Module_star_list[num],Module_star_list[num+1]):
      if re.match(r'.*@name\s(.*)\s-.*', fn[n]):  # extract the register name
          Register_name=re.match(r'.*@name\s(.*)\s-.*', fn[n])
          if '-' in Register_name[1]:
              Reg_name=re.split(r'\s-',Register_name[1])
              R_name=Reg_name[0]
          else:
              R_name=Register_name[1]
          Register_star_list.append(n)
          Register_len_list.append(R_name.count('_')+1)
          Module_Register_len_list.append((R_name.count('_')+1)+Module_name_len_list[num])
          Register_list.append(R_name)
          line_list.append(str(n))  # find the start line of register
    Module_count_register.append(Register_list)
    Register_list=[]

for kk in range(Register_star_list[len(Register_star_list)-1],len(fn)):  # find the last register end line
    if 'Masks' in fn[kk]:
        Mask_end=kk
Register_star_list.append(Mask_end)
for R in range(len(Module_count_register)):  # count the resister num of every module
    Module_Register_num.append(len(Module_count_register[R]))

Bit_list=[]
Mask_list=[]
# make the list of every register bit field
for num in range(len(Register_star_list) - 1):
    for n in range(Register_star_list[num],Register_star_list[num+1]):
        if re.match(r'^(.*)\(0x(.*)U\)\s+$',fn[n]):
            Bit = re.split(r'\s+', fn[n])
            Bit_line = re.split(r'_', Bit[1])
            line_number = list(range(len(Bit_line)))
            for n in range(Module_Register_len_list[num]):
             bit_number = line_number.pop(0)  # remove module name and register name
            bit_number = line_number.pop(-1)
            Bit_name = ''
            if re.match(r'\(0x(.*)U\)$', Bit[2]):  # extract mask value
                m = re.match(r'\(0x(.*)U\).*', Bit[2])
                bit_field=bin(int(m[1], 16)).count('1') - 1 +bin(int(m[1], 16)).count('0') - 1  # find out the bit field
                if bit_field == (bin(int(m[1], 16)).count('0') - 1):
                    Mask_vaule=str(bit_field)
                else:
                    Mask_vaule=str(bit_field)+ '-' + str(bin(int(m[1], 16)).count('0') - 1)
            for N in line_number:  # extract the bit name
                Bit_name = Bit_name + Bit_line[N] + '_'
            if len(Bit_name) == 0:
                pass
            else:
                Bit_list.append(Bit_name[:-1])
                Mask_list.append(Mask_vaule)
    Bit_name = dict(zip(Mask_list,Bit_list))
    Bit_mask_list.append(Bit_name)
    Bit_list=[]
    Mask_list=[]

# build the dict of module-register-bit
L=[]
for num in Module_Register_num:  # Merge registers for each module
    number=num+add
    for n in range(add,number):
        add=number
        Module_Register_list.append(Bit_mask_list[n])
    Module_link_Register_list.append(Module_Register_list)
    Module_Register_list = []

for i in range(len(Module_count_register)):  # build DataFrame of bit information
    rec = zip(Module_count_register[i],Module_link_Register_list[i],line_list)
    data = pandas.DataFrame(list(rec), columns=['name','bit_field','line'])
    L.append(data)
items=[(Module_name_list,L)]
Header_register_list=dict(zip(Module_name_list,L))
# print(Header_register_list)
# H=Header_register_list.get('CSI')
# print(H)

# get offset,name,width and Access of registers
offset_start_list=[]
access_star_list=[]
access_end_list=[]
module_access=[]
access_list=[]
for line in fn:
    if 'Register Layout Typedef' in line:  # find out the start line of every module register part
        if 'struct'in fn[fn.index(line)+1]:
            offset_start_list.append(fn.index(line))
    if 'Peripheral instance base addresses 'in line:
        if '0x' in fn[fn.index(line) + 2]:
         access_star_list.append(fn.index(line))
    if 'Peripheral_Access_Layer */' in line:
        access_end_list.append(fn.index(line))

Module_name=[]
name_list=[]
for num in range(len(access_star_list)):
    for n in range(access_star_list[num], access_end_list[num]):
            if re.match(r'#define\s(.*)_.*\(0x(.*)u\)',fn[n]):
                base_address=re.match(r'#define\s(.*)_.*\(0x(.*)u\)',fn[n])
                Module_name.append(base_address[1])
                module_access.append(base_address[2])
    access_list.append(module_access)
    name_list.append(Module_name)
    module_access=[]
    Module_name=[]

Module_access_list=[]
Module=[]
for n in range(len(access_list)):
    for p in range(len(access_list[n])):
        base=access_list[n][p][:4]+'_'+access_list[n][p][4:]
        Module_access_list.append(base)
        Module.append(name_list[n][p])
Header_module_base=dict(zip(Module,Module_access_list))
# print(Header_module_base)

offset_list=[]
Table_Register_name=[]
Width=[]
Access=[]
line=[]
Header_module_list_All=[]

for num in range(len(offset_start_list)):
    for n in range(offset_start_list[num], Module_star_list[num]):
         if re.match(r'.*uint(.*)_t\s(.*);.*offset:\s0x(.*)\s\*\/',fn[n]):
             A=re.match(r'.*uint(.*)_t\s(.*);.*offset:\s0x(.*)\s\*\/',fn[n])
             if '__' in A[0]:
                 AA=re.match(r'.*__(.*)uint(.*)_t\s(.*);.*offset:\s0x(.*)\s\*\/',A[0])
                 get_offset=AA[4]
                 get_name=AA[3]
                 get_width=AA[2]
                 get_IO=AA[1]
             else:
                 get_offset=A[3]
                 get_name=A[2]
                 get_width = A[1]
                 get_IO='--'
             line.append(n+1)
             if ','in get_offset:
                 B=re.split(',',get_offset)
                 offset = B[0] + 'h'
                 if len(access_list[num])>1:
                     for ee in range(len(access_list[num])):
                             offset = offset + '|' + hex(int(B[0], 16) + int(access_list[num][ee], 16))[2:].upper()[
                                                     :4] + '_' + hex(
                                 int(B[0], 16) + int(access_list[num][ee], 16))[2:].upper()[
                                                             4:]  # get the offset of every register
                 else:
                     offset = B[0] + 'h'
                     offset=offset+ '|' + hex(int(B[0], 16) + int(access_list[num][0], 16))[2:].upper()[
                                                     :4] + '_' + hex(
                                 int(B[0], 16) + int(access_list[num][0], 16))[2:].upper()[
                                                             4:]

             else:
                 offset = get_offset+'h'
                 if len(access_list[num]) > 1:
                     for ee in range(len(access_list[num])):
                         offset = get_offset + '|' + offset + '|' + hex(int(get_offset,16)+int(access_list[num][ee],16))[2:].upper()[:4]+'_'+hex(int(get_offset,16)+int(access_list[num][ee],16))[2:].upper()[4:]  # 获得每一个寄存器的Address_offset
                 else:
                       offset = get_offset + '|' + offset+'|' + hex(int(get_offset,16)+int(access_list[num][0],16))[2:].upper()[:4]+'_'+hex(int(get_offset,16)+int(access_list[num][0],16))[2:].upper()[4:]
             offset_list.append(offset)
             Table_Register_name.append(get_name)
             Width.append(get_width)
             if 'IO' in get_IO:
                 IO = 'R/W'+'|'+'RW'+'|'+'W1C'+'|'+'RWONC E'+'|'+'w1C'
             elif 'I'in get_IO:
                 IO='R'+'|'+'RO'
             elif'O'in get_IO:
                 IO='W''|'+'WO'+'|'+'W\r(always\rreads 0)'
             elif '--' in get_IO:
                 IO='--'
             Access.append(IO)
    rec=zip(offset_list,Table_Register_name,Width,Access,line)
    data=pandas.DataFrame(list(rec), columns = ['Address', 'Name', 'Width', 'Access','line'])
    Header_module_list_All.append(data)
    offset_list=[]
    Table_Register_name=[]
    Width = []
    Access = []
    line=[]
Header_module_list_all=dict(zip(Module_name_list,Header_module_list_All))
H_data=Header_module_list_all.get('VPU_H1')

Header_test_info.write('Peripheral base address \n')  # write base address into txt
for k, v in Header_module_base.items():
    ss = k + '  ' + v + '\n'
    Header_test_info.write(ss)

for k, v in Header_module_list_all.items():  # write module_list into HTML
    Header_test_module.write(k+'<br>')
    T=v.to_html()
    Header_test_module.write(T+'<br>')

for k, v in Header_register_list.items():  # write module_list into HTML
    Header_test_bit.write(k+'<br>')
    pandas.set_option('max_colwidth', 1000)
    T=v.to_html()
    Header_test_bit.write(T+'<br>')


for i in Module_name_list:
    M_name=i + '\n'
    M.write(M_name)

M.close()


# for xx in range(len(Module_H)):
#   B=Module_H[xx].replace('I2S','I2S|SAI ')
#   print(B)
# print(Header_module_base)
# test_module = open('t.html','r')
# Y=pandas.read_html('t.html')
# Z=test_module.read()
# print(Y[0])
# print(Z)


# # check the num of RESERVED is correct or not Reserve_list=[] Reserve_given_num_list=[] Reserve_count_num_list=[]
# for num in range(len(offset_start_list)): for n in range(offset_start_list[num], Module_star_list[num]): if
# 'RESERVED'in fn[n]: if re.match(r'.*RESERVED_.*\[(.*)\]',fn[n]):  # extract the num of RESERVED
# Reserve_given_num=re.match(r'.*RESERVED_.*\[(.*)\]',fn[n]) Reserve_given_num_list.append(Reserve_given_num.group(
# 1)+':'+str(n+1)) if re.match(r'.*uint(.*)_t.*', fn[n - 1]) or re.match(r'.*offset:(.*)\s\*/', fn[n-1]) :  # extract
# the offset and size of last register size=re.match(r'.*uint(.*)_t.*', fn[n - 1]) Register_size=int(int(size.group(
# 1))/8) offset_vaule = re.match(r'.*offset:\s0x(.*)\s\*/', fn[n - 1]) offset = re.split(r',',offset_vaule.group(1))
# previous_offset = int(offset[0], 16) else: if "typedef"in fn[n-1]:  # the situation of RESERVED exist in the start
# of the module Register_size=0 previous_offset=0 else: if ']'in fn[n-1]: channel_number=re.match(r'.*\[(.*)\]',
# fn[n-1])  # the situation of channel exist channel=int(channel_number.group(1))-1 elif re.match(r'.*\[(.*)\]',
# fn[n - 2]): print(fn[n - 2]) channel_number = re.match(r'.*\[(.*)\]', fn[n - 2]) channel = int(
# channel_number.group(1)) - 1 else: channel=0 if 'array' in fn[n - 2]: step = re.match(r'.*array\sstep:\s0x(
# .*)\s\*/', fn[n - 2]) array_step = int(step.group(1),16) array_offset_vaule = re.match(r'.*offset:\s0x(.*),.*',
# fn[n - 2]) array_offset=int(array_offset_vaule.group(1),16) size = re.match(r'.*uint(.*)_t.*', fn[n - 2])
# Register_size = int(int(size.group(1)) / 8) total_offset=int(channel*array_step) m = re.match(r'.*offset:\s0x(
# .*)\s\*/', fn[n - 2]) offset = re.split(r',', m.group(1)) previous_offset = int(offset[0],
# 16) previous_offset=previous_offset+total_offset if re.match(r'.*_t\s(.*)];.*', fn[n-1]):  # the situation of array
# exist array = re.match(r'.*_t\s(.*);.*', fn[n-1]) array_index=(array.group(1).count('['))+1 array_num=re.split(r'\[
# ',array.group(1)) array_total = 1 for U in range(1,array_index): array_total=(int(array_num[U][:-1]))*array_total
# array_total_size=(array_total-1)*Register_size else: array_total_size=0 if re.match(r'.*offset:(.*)\s\*/',
# fn[n + 1]):  # extract the offset after RESERVE m = re.match(r'.*offset:(.*)\s\*/', fn[n+1]) offset = re.split(r',
# ', m.group(1)) Forward_offset=int(offset[0],16) elif re.match(r'.*\[(.*)\]',fn[n+1]):   # the situation of array
# exist a=re.match(r'.*\[(.*)\]',fn[n+1]) if re.match(r'.*uint(.*)_t.*0x(.*),.*0x(.*)\s\*\/',fn[n-1]): b=re.match(
# r'.*uint(.*)_t.*0x(.*),.*0x(.*)\s\*\/',fn[n-1]) pls=(int(A(1))-1)*int(b.group(3),16) if re.match(r'.*0x(.*)\s\*\/',
# fn[n+2]): c=re.match(r'.*0x(.*)\s\*\/',fn[n+2]) Forward_offset=int(c.group(1),16)-pls Reserve_count_num=str(
# Forward_offset-previous_offset-Register_size-array_total_size)+':'+str(n+1) Reserve_count_num_list.append(
# Reserve_count_num)
#
# for num in range(len(Reserve_count_num_list)):
#     Reserve_given=re.split(r':',Reserve_given_num_list[num])
#     Reserve_count=re.split(r':',Reserve_count_num_list[num])
#     if Reserve_count ==Reserve_given:
#         pass
#     else:
#       print("reserved number is wrong,please check line:",Reserve_given[1])

# ###Get interrupt num and name###
# for line in fn:  # find the star and end line of interrupt list
#     if 'Auxiliary constants'in line:
#         core_interrupt=fn.index(line)
#     if 'Device specific interrupts'in line:
#         interrupt_start=fn.index(line)+1
#     if 'IRQn_Type' in line:
#         interrupt_end=fn.index(line)
#
# Device_interrupt_name_list=[]
# Device_interrupt_number_list=[]
# core_interrupt_name_list=[]
# core_interrupt_number_list=[]
# for n in range(core_interrupt,interrupt_end):  # extract the name,num and note of interrupt to build the dict
#     if 'IRQn'in fn[n]:
#         J = re.split(r'\s+', fn[n])
#         if re.match(r'.*\<\s(.*)\s\*', fn[n]):
#             get_description = re.match(r'.*\<\s(.*)\s\*', fn[n])
#         if n < interrupt_end - 1:
#             number = int(J[3][:-1])
#         else:
#             number = int(J[3])
#         if number<0:
#             core_interrupt_name_list.append(J[1])
#             if 'Cortex-'in get_description.group(1):
#                 A=re.split(r' ',get_description.group(1))
#                 ARM_resion=A[0][7:9]
#             core_interrupt_number_list.append(str(number) + ',' + get_description.group(1))
#             core_interrupt_table = dict(zip(core_interrupt_name_list, core_interrupt_number_list))  # extract the ARM interrupt to build a list
#         else:
#             Device_interrupt_name_list.append(J[1])
#             Device_interrupt_number_list.append(str(number) + ',' + get_description.group(1))
#             Device_interrupt_table = dict(zip(Device_interrupt_name_list, Device_interrupt_number_list)) # extract the name,num and note of interrupt to build the dict
# M0={'NotAvail_IRQn': '-128,Not available device specific interrupt', 'NonMaskableInt_IRQn': '-14,Non Maskable Interrupt', 'HardFault_IRQn': '-13,Cortex-M0 SV Hard Fault Interrupt', 'SVCall_IRQn': '-5,Cortex-M0 SV Call Interrupt', 'PendSV_IRQn': '-2,Cortex-M0 Pend SV Interrupt', 'SysTick_IRQn': '-1,Cortex-M0 System Tick Interrupt'}
# M4={'NotAvail_IRQn': '-127,Not available device specific interrupt', 'NonMaskableInt_IRQn': '-14,Non Maskable Interrupt', 'HardFault_IRQn': '-13,Cortex-M4 SV Hard Fault Interrupt', 'MemoryManagement_IRQn': '-12,Cortex-M4 Memory Management Interrupt', 'BusFault_IRQn': '-11,Cortex-M4 Bus Fault Interrupt', 'UsageFault_IRQn': '-10,Cortex-M4 Usage Fault Interrupt', 'SVCall_IRQn': '-5,Cortex-M4 SV Call Interrupt', 'DebugMonitor_IRQn': '-4,Cortex-M4 Debug Monitor Interrupt', 'PendSV_IRQn': '-2,Cortex-M4 Pend SV Interrupt', 'SysTick_IRQn': '-1,Cortex-M4 System Tick Interrupt'}
# M7={'NotAvail_IRQn': '-128,Not available device specific interrupt', 'NonMaskableInt_IRQn': '-14,Non Maskable Interrupt', 'HardFault_IRQn': '-13,Cortex-M7 SV Hard Fault Interrupt', 'MemoryManagement_IRQn': '-12,Cortex-M7 Memory Management Interrupt', 'BusFault_IRQn': '-11,Cortex-M7 Bus Fault Interrupt', 'UsageFault_IRQn': '-10,Cortex-M7 Usage Fault Interrupt', 'SVCall_IRQn': '-5,Cortex-M7 SV Call Interrupt', 'DebugMonitor_IRQn': '-4,Cortex-M7 Debug Monitor Interrupt', 'PendSV_IRQn': '-2,Cortex-M7 Pend SV Interrupt', 'SysTick_IRQn': '-1,Cortex-M7 System Tick Interrupt'}
#
# if ARM_resion =='M0':
#     Core=M0
# elif ARM_resion=='M4':
#     Core=M4
# elif ARM_resion=='M7':
#     Core=M7
# else:
#     print('the core is :',ARM_resion)
#
#
# core_list=[]
# device_list=[]
# if len(core_interrupt_table)==len(Core):
#     for kv in core_interrupt_table.items():
#        core_list.append(kv)
#     for kz in Core.items():
#        device_list.append(kz)
# else:
#     print('core interrupt number is wrong')
#
# for n in range(len(Core)):
#     if core_list[n]==device_list[n]:
#         pass
#     else:
#         print(device_list[n])
# print(list(Header_register_list.get('ADC').iat[0, 1].keys()))

