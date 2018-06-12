#!/user/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Andy Xu'
'''
python version : V3 (3.6.2)
this script use the chrome as download browser ,you should download chromedriver compressed file which suitable your
using chrome version from http://npm.taobao.org/mirrors/chromedriver/ ,unzip this file and add it to the installation path of chrome
'''
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
import os,time

# C:\Users\nxf32672\Desktop\python_exercise\download.txt
# TestFilePath = input('please input the path of test file which contain boards and processor list ,end with Enter key :')
# BoardList = []
# ProcessorList = []
# fp = open(TestFilePath,'r')
# x = 0
# for line in fp.readlines():
#     if (x == 1) & ('rocessor' not in line) & (len(line) > 3):
#         ProcessorList.append(line.strip())
#     if (x == 2) & ('oard' not in line) & (len(line) > 3):
#         BoardList.append(line.strip())
#     if 'oard' in line:
#         x = 1
#     if 'rocessor' in line:
#         x = 2
# fp.close()
chromedriver = 'C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe'
os.environ['webdriver.chrome.driver'] = chromedriver
driver = webdriver.Chrome(chromedriver)
driver.get('http://kex-stage.freescale.net/en/select')

# USERname = input('please input your user name , and end with Enter key :')
# USERpassword = input('please input your user password , and end with Enter key :')

driver.find_element_by_id('username').clear()
driver.find_element_by_id('username').send_keys('nxf32672')
driver.find_element_by_id('password').clear()
driver.find_element_by_id('password').send_keys('ACEanan@0903')
driver.find_element_by_name('loginbutton').click()
driver.maximize_window()
#小窗口运行程序会出错

# for boardname in BoardList:
time.sleep(2)
driver.find_element_by_id('select-search').clear()
driver.find_element_by_id('select-search').send_keys('LPCXpresso54018')
# board-select
driver.find_element_by_xpath('//*[@id="select-tree"]/ul/li[4]').click()
time.sleep(2)
# build SDK
SelectButton = driver.find_element_by_xpath('//*[@id="select-button"]')
ActionChains(driver).click(SelectButton).perform()
time.sleep(2)
# OS select--Window
# 下拉菜单用法：https://www.cnblogs.com/fnng/p/5361443.html
sel_win = driver.find_element_by_xpath('//*[@id="os-option"]')
Select(sel_win).select_by_value('os-windows')

# Toolchain select all development
ToolChainAll = driver.find_element_by_xpath('//*[@id="toolchains_2.3.0"]')
Select(ToolChainAll).select_by_value('all')

# select option middleware
time.sleep(2)
AddSoftwareComponentButton = driver.find_element_by_xpath('//*[@id="add-comp"]/i').click()
ActionChains(driver).click(AddSoftwareComponentButton).perform()


# Actions action = new Actions(chrome)
# action.moveToElement(chrome.findElement(By.id("cust")  )).perform()// 鼠标移动到 toElement 元素中点
# Thread.sleep(1000)
# chrome.findElement(By.id("list_2") ).click() // 【XX列表】click事件
# chrome.manage().window().maximize() // 窗口最大化
# action.release()// 鼠标事件释放


# driver.close()
# driver.quit()
