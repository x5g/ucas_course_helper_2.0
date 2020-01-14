# -*- coding: utf-8 -*-
# @Date    : 2020年01月08日20:51:25
# @Author  : czx
from __future__ import print_function
import re
import time

from LoginUCAS import LoginUCAS


class NoLoginError(Exception):
    pass


class NotFoundCourseError(Exception):
    pass


class NotSelectCourseTime(Exception):
    pass


class UcasCourse(object):
    def __init__(self):
        self.session = None
        self.headers = None
        self.jwxk_html = None
        self.course = UcasCourse._read_course_info()
        self._init_session()

    def _init_session(self):
        t = LoginUCAS().login_sep()
        self.session = t.session
        self.headers = t.headers
        self.login_jwxk()

    @classmethod
    def _read_course_info(self):
        with open("./private.txt") as f:
            courses = []
            for i, line in enumerate(f):
                if i < 2: continue
                courses.append(line.strip().split())
        print(courses)
        return courses

    def login_jwxk(self):
        # 从sep中获取Identity Key来登录选课系统，进入选课选择课学院的那个页面
        url = "http://sep.ucas.ac.cn/portal/site/226/821"
        r = self.session.get(url, headers=self.headers)
        try:
            code = re.findall(r'"http://jwxk.ucas.ac.cn/login\?Identity=(.*)"', r.text)[0]
        except IndexError:
            raise NoLoginError

        url = "http://jwxk.ucas.ac.cn/login?Identity=" + code
        self.headers['Host'] = "jwxk.ucas.ac.cn"
        self.session.get(url, headers=self.headers)
        url = 'http://jwxk.ucas.ac.cn/courseManage/main'
        r = self.session.get(url, headers=self.headers)
        self.jwxk_html = r.text

    def get_course(self):
        # 获取课程开课学院的id，以及选课界面HTML
        html = self.jwxk_html
        if not str.isdigit(self.course[0][0]):  # 第一个参数非数字的话，则为中文（如计算机学院）
            regular = r'<label for="id_([\S]+)">' + self.course[0][0]
            institute_id = re.findall(regular, html)[0]
        else:   # 否则第三个参数为数字，如951→对应计算机学院的id
            institute_id = self.course[0][0]

        url = 'http://jwxk.ucas.ac.cn' + \
              re.findall(r'<form id="regfrm2" name="regfrm2" action="([\S]+)" \S*class=', html)[0]
        post_data = {'deptIds': institute_id, 'sb': '0'}

        html = self.session.post(url, data=post_data, headers=self.headers).text
        return html, institute_id

    def select_course(self):
        if not self.course: return None
        # 选课，主要是获取课程背后的ID
        html, institute_id = self.get_course()
        if html.find('<label id="loginError" class="error">未开通选课权限</label>') != -1:
            raise NotSelectCourseTime
        url = 'http://jwxk.ucas.ac.cn' + \
              re.findall(r'<form id="regfrm" name="regfrm" action="([\S]+)" \S*class=', html)[0]
        # sid = re.findall(r'<span id="courseCode_([\S]+)">' + self.course[0][0] + '</span>', html)
        sid = []    # 存课程编码
        for i in range(1, len(self.course[0])):
            sidelem  = re.findall(r'<span id="courseCode_([\S]+)">' + self.course[0][i] + '</span>', html)
            if sidelem:
                sid.append(sidelem)
            else:
                raise NotFoundCourseError

        # if sid:
        #     sid = sid[0]
        # else:
        #     raise NotFoundCourseError

        post_data = {'deptIds': institute_id, 'sids': sid}
        # if self.course[0][1] == '1':
        #     post_data['did_' + sid] = sid

        html = self.session.post(url, data=post_data, headers=self.headers).text
        # if html.find(u'选课成功') != -1:
        #     return self.course.pop(0)[0]
        # else:  # 一般是课程已满
        #     info = re.findall('<label id="loginError" class="error">(.+)</label>', html)[0]
        #     print(info)
        #     return None

        # 返回选课结果
        print(self.course[0][0] + "的选课结果为:")
        error = re.findall('<label id="loginError" class="error">(.+)</label>', html)
        success = re.findall('<label id="loginSuccess" class="success">(.+)</label>', html)
        print("error：", error)
        print("success: ", success)
        return self.course.pop(0)

    def sleep(self, t=5):
        time.sleep(t)

    def start(self):
        while True:
            try:
                res = self.select_course()
                # if res is not None:
                #     print('课程编号为 {} 的选课成功'.format(res))
                # elif not self.course:
                if res is None:
                    print('全部选完')
                    exit(0)
                else:
                    self.sleep()
            except NoLoginError:
                self._init_session()
            except NotFoundCourseError:
                print('尝试选择学院为 {} 的时候出错，可能编号错误或者已被选上'.format(self.course.pop(0)[0]))
            except NotSelectCourseTime:
                print('选课时间未到')
                self.sleep(20)
            except Exception as e:
                print(e)
                self.sleep()
                self._init_session()


if __name__ == '__main__':
    # while datetime.datetime.now() < datetime.datetime(2017, 6, 1, 12, 10, 00):
    #     print('wait ',datetime.datetime.now())
    #     time.sleep(60)
    UcasCourse().start()