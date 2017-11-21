from bs4 import BeautifulSoup
import requests
import csv

class FDroid_Crawler:

    def __init__(self):
        self.domain = "http://f-droid.org"
        self.linklist = []
        self.linklist.append("http://f-droid.org/en/packages/index.html")
        for i in range(2,47):
            link = "http://f-droid.org/en/packages/"+str(i)+"/index.html"
            self.linklist.append(link)

        #process these links
        self.prcoess_links(self.linklist)



    def get_app_size_mb(self, app_size):
        if "MiB" in app_size:
            real_size = app_size[:len(app_size)-len("MiB")]
            return real_size
        elif "KiB" in app_size:
            real_size = app_size[:len(app_size)-len("KiB")]
            real_size_float = float(real_size)
            real_size_float = real_size_float/1024
            return str(real_size_float)
        elif "GiB" in app_size:
            real_size = app_size[:len(app_size)-len("GiB")]
            real_size_float = float(real_size)             # raise errors to process
            real_size_float = real_size_float*1024
            return real_size_float
        else:
            raise Exception("need to add unknown type:",app_size)


    def prcoess_links(self,linklist):
        # get all apps in the list

        appid_index = 1

        file = open("froid.csv","a")
        froidwriter = csv.writer(file)
        froid_header = ['app_id','package','app_name','version','permission'
                        ,'source_code_url','size(M)','googleplay_url','num_installation','app_category']
        froidwriter.writerow(froid_header)
        print("process start...")
        for url in linklist:
            #print(url)
            url_page = requests.get(url)

            # url_page.data is the result
            url_page_soup = BeautifulSoup(url_page.content, "html.parser")

            # get the list of package names
            for packageheader in url_page_soup.find_all(attrs={'id':'full-package-list'}):
                for link in packageheader.find_all(attrs={'class':'package-header'}):
                    result_list = []
                    relative_package_url = link.get('href')

                    # the target url of the package
                    full_package_url = self.domain+relative_package_url


                    #（1） app id
                    app_id = appid_index
                    appid_index+=1
                    result_list.append(app_id)

                    # (2) get the package name
                    package_name = relative_package_url[1+relative_package_url.rindex('/'):]

                    result_list.append(package_name)
                    print("process package:",package_name)

                    package_page = requests.get(full_package_url)
                    package_soup = BeautifulSoup(package_page.content, "html.parser")
                    # (3) app name
                    app_name = package_soup.find(attrs={'class':"package-name"}).text.strip()
                    result_list.append(app_name)

                    # (4) version
                    app_version_header = package_soup.find(attrs={'class':'package-version-header'})
                    app_version = app_version_header.find('b').text.strip()
                    app_version = app_version[len("Version")+1:]
                    result_list.append(app_version)

                    # (5) permission
                    app_permission = []
                    app_permission_str = ""
                    webpage_permission_list = package_soup.find(attrs={'class':'package-version-permissions-list'})
                    webpage_app_permission_text_list = webpage_permission_list.find_all('li')
                    for permission in webpage_app_permission_text_list:
                        app_permission.append(permission.text.strip())
                        app_permission_str += str(permission.text.strip())
                        app_permission_str += ";"

                    if app_permission_str.strip() == "":
                        app_permission_str = "Nil"

                    result_list.append(app_permission_str)


                    # (6) source code url
                    app_source_code_url = ""
                    package_related_links = package_soup.find(attrs={'class':'package-links'})
                    package_related_links_array = package_related_links.find_all(attrs={'class':'package-link'})

                    for package_related_link in package_related_links_array:
                        href_div = package_related_link.find("a",href=True)
                        href_div_text = href_div.text.strip()
                        if href_div_text == "Source Code":
                            app_source_code_url = href_div['href']
                            break

                    if app_source_code_url.strip() == "":
                        app_source_code_url = "Nil"

                    result_list.append(app_source_code_url)

                    # (7) size
                    package_version_download_div = package_soup.find_all(attrs={'class':'package-version-download'})
                    package_version_download_div_first = package_version_download_div[0]
                    app_size = self.get_app_size_mb(str(package_version_download_div_first.find_all("a")[0].next_sibling).strip())
                    result_list.append(app_size)

                    # (8) google play url
                    # https://play.google.com/store/apps/details?id=com.markuspage.android.atimetracker&hl=en
                    google_play_url = "https://play.google.com/store/apps/details?id="+package_name+"&hl=en"

                    google_play_url_request = requests.get(google_play_url)
                    google_play_url_soup = BeautifulSoup(google_play_url_request.content,"html.parser")
                    found_not_match_statement = google_play_url_soup.findAll(text="We're sorry, the requested URL was not found on this server.")
                    # number of installation

                    if len(found_not_match_statement)>=1:
                        on_google = False
                    else:
                        google_search_request = requests.get("https://play.google.com/store/search?q="+package_name+"&c=apps&hl=en")
                        google_search_soup = BeautifulSoup(google_search_request.content, "html.parser")
                        search_found_not_match_statement = google_search_soup.findAll(attrs={'class':'empty-search'})
                        if len(search_found_not_match_statement)>=1:
                            on_google = False
                        else:
                            on_google = True


                    if not on_google:
                        google_play_url = "Nil"
                        result_list.append(google_play_url)
                        num_installation = "Nil"
                        result_list.append(num_installation)
                        app_category = "Nil"
                        result_list.append(app_category)
                        froidwriter.writerow(result_list)
                        continue

                    result_list.append(google_play_url)

                    num_download_div = google_play_url_soup.find(attrs={'itemprop':'numDownloads'})
                    num_download = num_download_div.text.strip()
                    result_list.append(num_download)

                    # app category
                    app_category_div = google_play_url_soup.find(attrs={'class':'document-subtitle category'})
                    app_category = app_category_div.find(attrs={'itemprop':'genre'}).text
                    result_list.append(app_category)
                    froidwriter.writerow(result_list)


        file.close()
        print("process finish")
        print("=====================")
        print("in total, we obtain:%d apps",appid_index-1)


if __name__ == '__main__':
    fdroid_crawler = FDroid_Crawler()