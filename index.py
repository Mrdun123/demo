import requests, json, os
from lxml import etree


requests.packages.urllib3.disable_warnings()
url = 'https://www.bilibili.com/video/av40672186'

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'
}



def getbilibilivideourl(url):
    res = requests.get(url, headers = headers).content.decode()
    selector = etree.HTML(res)
    scripts = selector.xpath('//script/text()')
    videoplayinfo = json.loads(scripts[3][20:])
    playinfo = videoplayinfo['data']['dash']
    videourl = playinfo['video'][0]['baseUrl']
    audiourl = playinfo['audio'][0]['baseUrl']
    return videourl, audiourl



def filedownload(refererurl, fileurl, name, session = requests.Session()):
    headers.update({'referer': refererurl})
    session.options(url = fileurl, headers = headers, verify = False)

    # range 的开始-结尾
    # 每次下载1Mb的数据
    start = 0
    end = 1024*512-1
    # 判断是否要跳出循环
    flag = 0
    while True:
        # 添加range请求头
        headers.update({'range': 'bytes=' + str(start)+'-'+str(end)})
        res = session.get(fileurl, headers = headers, verify = False)
        if res.status_code != 416:
            start = end + 1
            end = end + 1024*512
        else:
            headers.update({'range': 'bytes=' + str(start)+'-'})
            res = session.get(fileurl, headers = headers, verify = False)
            flag = 1
        with open('./video/' + name, 'ab') as f:
            f.write(res.content)
            f.flush()
        if flag:
            break


def main():
    name = str(input('请输入Bv号：'))
    url = 'https://www.bilibili.com/video/' + name
    video, audio = getbilibilivideourl(url)
    s = requests.Session()
    filedownload('https://www.bilibili.com/', video, 'video.m4s', session=s)
    filedownload('https://www.bilibili.com/', audio, 'audio.m4s', session=s)
    return name

if __name__ == '__main__':
    name = main()
    # os.system('ffmpeg -i ./video/video.m4s -i ./video/audio.m4s -codec copy ./video/' + name + '.mp4')
    # os.remove('./video/video.m4s')
    # os.remove('./video/audio.m4s')
    print('视频下载完成！')

