#!/usr/bin/python3
"""Main class for the course scraper.
"""
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from course import Course
from database import Database
import requests
import time
import csv

baseUrl = "http://www.courseatlas.com/SearchCoursesOnline/CourseSearchResults/tabid/135/Default.aspx?instnm={0}&distance=5&page={1}&perpage=50"


def getPage(url):
    """Get the requested page and return a BeautifulSoup object"""
    print("Retrieving URL:\n"+url)
    session = requests.Session()
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}
    try:
        req = session.get(url, headers=headers)
        if req.status_code is 429:
            time.sleep(5)
            return getPage(url)
    except requests.exceptions.RequestException:
        return None
    bsObj = BeautifulSoup(req.text, "lxml")
    return bsObj

def parseCourse(pageUrl):
    """Parse course information from the page and return a course object"""
    time.sleep(3)
    bsObj = getPage(pageUrl)
    title = bsObj.find("span",id="dnn_ctr1713_CourseInfo_Label1")
    institution = bsObj.find("span",id= "dnn_ctr1713_CourseInfo_Label4")
    subject = bsObj.find("span",id="dnn_ctr1713_CourseInfo_Label14")
    description = bsObj.find("span",id="dnn_ctr1713_CourseInfo_Label16")
    title = title.get_text() if title is not None else ""
    institution = institution.get_text() if institution is not None else ""
    subject = subject.get_text() if subject is not None else ""
    description = description.get_text() if description is not None else ""
    this_course = Course(None, title, subject, description, institution)
    return this_course

def saveCourses(pageUrl, institution, db):
    """Find course page links in the provided page and save to a database"""
    bsObj = getPage(pageUrl)
    raw_courses = bsObj.find("ul",{"class","student-course-search-results-list"}).find_all("li")
    for raw_course in raw_courses:
        course = parseCourse(raw_course.find("a").attrs["href"])
        course.institution = institution[1]
        course.save(db)

def getPages(institutionName):
    """Get number of page results for the given institution"""
    bsObj = getPage(baseUrl.format(institutionName,1))
    lastPage = bsObj.find("a",{"class","a1-pager-last"})
    lastLink = lastPage.attrs["href"]
    return int(lastLink[lastLink.rfind("page=")+5:])

def getSchool(institution, db):
    """Save all courses for a given institution"""
    pages = getPages(institution[0])
    for page in range(1,pages):
        saveCourses(baseUrl.format(institution[0], page), institution, db)


db = Database()
institutionsFile = open("institutions.csv")
institutions = institutionsFile.read()
institutions = institutions.split('\n')
institutionsAbvrs = []
institutions.pop(0)
for institution in institutions:
    getSchool(institution.split(','), db)
