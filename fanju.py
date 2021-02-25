import requests, os, json, re, time
from threading import Thread, BoundedSemaphore
from lxml import etree

requests.packages.urllib3.disable_warnings()

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
    'referer': 'https://www.bilibili.com/bangumi/play/ss34430',
    'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en-GB;q=0.7,en;q=0.6,ja;q=0.5',
    # 'cookie': 'l=v; _uuid=CB42331A-B79E-9AA6-41CA-120E0474FC4E78500infoc; LIVE_BUVID=AUTO7915845253315605; buvid3=73EED969-391E-4CA7-A6C5-D3CACD249E4453936infoc; blackside_state=1; sid=jmulc70z; CURRENT_QUALITY=0; CURRENT_FNVAL=80; DedeUserID=358351579; DedeUserID__ckMd5=83033d235ffe77cf; SESSDATA=9dd35dcf^%^2C1616046424^%^2C72e70*91; bili_jct=b0922bb96e9a8c62a712d446ce5a7565; rpdid=^|(um~kmRYmmm0J\'uY^|YJuYlmY; fingerprint3=63b58623620c36159cacd01907027b73; buvid_fp_plain=73EED969-391E-4CA7-A6C5-D3CACD249E4453936infoc; buivd_fp=73EED969-391E-4CA7-A6C5-D3CACD249E4453936infoc; bp_video_offset_358351579=487548349386845187; balh_server_inner=__custom__; balh_is_closed=; balh_server_custom_hk=https://bili-proxy.98e.org; balh_server_custom_tw=https://app.bili.link; balh_server_custom_cn=https://1985592077837091.cn-shanghai.fc.aliyuncs.com/2016-08-15/proxy/bili/bili_prox; fingerprint=ae511f96e94547a4feb03a9e1e811cc9; fingerprint_s=fe2108b2a61efd8159b488de3654efe6; buvid_fp=73EED969-391E-4CA7-A6C5-D3CACD249E4453936infoc; balh_mode=redirect; bp_t_offset_358351579=493739003583855108; PVID=3',
    'Referer': 'https://www.bilibili.com/bangumi/play/ss34430',
}

def filedown(url, ep_id, type, session):
    session.options(url, headers=headers, verify=False)

    flag = 0

    start = 0
    end = 1024*512-1
    name = str(ep_id) + type
    while True:
        headers.update({'range': 'bytes='+str(start)+'-'+str(end)})
        res = session.get(url, headers=headers, verify=False)
        if res.status_code != 416:
            start = end+1
            end += 1024*512
        else:
            headers.update({'range': 'bytes='+str(start)+'-'})
            res = session.get(url, headers=headers, verify=False)
            flag = 1

        videowrite(name, res.content)
        if flag:
            break

def videowrite(name, item):

    try:
        with open(f'./video/{name}.m4s', 'ab') as f:
            f.write(item)
            f.flush()
    except Exception:
        print('下载错误')
        pass

def videohb(ep_id):
    videopath = f'./video/{ep_id}video.m4s'
    audiopath = f'./video/{ep_id}audio.m4s'
    os.system('ffmpeg -i %s -i %s -codec copy ./video/%d.mp4' % (videopath, audiopath, ep_id))
    os.remove(videopath)
    os.remove(audiopath)
    print(f'ep{ep_id}视频下载成功')

def get_allbaseurl(ss):
    '''
    列表中每个元素是个列表[ep_id, videourl, audiourl]，即[[ep_id, videourl, audiourl], ...]
    :param ss:
    :return:
    '''
    videosInfo = get_params(ss)
    allbaseurl = []
    for video in videosInfo:
        try:
            baseurl = []
            url = 'https://api.bilibili.com/pgc/player/web/playurl'
            # headers.update({'referer': 'https://www.bilibili.com/bangumi/play/ss34430'})

            params = {
                'cid': video[0],
                'qn': 0,
                'type': '',
                'otype': 'json',
                'fourk': 1,
                'bvid': video[1],
                'ep_id': video[2],
                'fnver': 0,
                'fnval': 80,
                # 'session': 'b745e7da69ddd52e92b7656e11394a88'
            }
            res = requests.get(url, headers=headers, params=params)
            data = res.json()
            videourl = data['result']['dash']['video'][0]['baseUrl']
            audiourl = data['result']['dash']['audio'][0]['baseUrl']
            baseurl.append(video[2])
            baseurl.append(videourl)
            baseurl.append(audiourl)
            allbaseurl.append(baseurl)
        except Exception:
            print('此集需要大会员')
    return allbaseurl

def get_baseurl(ss):
    videosInfo = get_params(ss)
    video = videosInfo[5]
    url = 'https://api.bilibili.com/pgc/player/web/playurl'
    params = {
        'cid': video[0],
        'qn': 0,
        'type': '',
        'otype': 'json',
        'fourk': 1,
        'bvid': video[1],
        'ep_id': video[2],
        'fnver': 0,
        'fnval': 80,
        # 'session': 'b745e7da69ddd52e92b7656e11394a88'
    }
    res = requests.get(url, headers=headers, params=params)
    data = res.json()
    videourl = data['result']['dash']['video'][0]['baseUrl']
    audiourl = data['result']['dash']['audio'][0]['baseUrl']
    return videourl, audiourl


def get_params(ss):
    url = f'https://www.bilibili.com/bangumi/play/{ss}'
    headers.update({'referer':''})
    res = requests.get(url, headers=headers).content.decode()
    selector = etree.HTML(res)
    script = selector.xpath('/html/body/script[5]/text()')[0]
    datas = re.search('window.__INITIAL_STATE__=(.*);\(function', script).group(1)
    data = json.loads(datas)
    eplist = data['epList']
    videosInfo = []
    for ep in eplist:
        videoInfo = []
        cid = ep['cid']
        bvid = ep['bvid']
        ep_id = ep['id']
        videoInfo.append(cid)
        videoInfo.append(bvid)
        videoInfo.append(ep_id)
        videosInfo.append(videoInfo)
    return videosInfo

def videoDown(videoInfo, session, lock):
    lock.acquire()
    wenjian = str(videoInfo[0])+'.mp4'
    if wenjian in os.listdir('./video/'):
        print(wenjian+'已存在')
        return
    filedown(videoInfo[1], videoInfo[0], 'video', session)
    filedown(videoInfo[2], videoInfo[0], 'audio', session)
    videohb(videoInfo[0])
    lock.release()


def mkdir():
    if not os.path.exists('./video'):
        os.mkdir('./video')


if __name__ == '__main__':
    # ss = 'ss37757'
    ss = input('请输入番剧ss号：')
    allbaseurl = get_allbaseurl(ss)
    lock = BoundedSemaphore(4)
    mkdir()
    works = []
    for baseurl in allbaseurl:
        session = requests.Session()
        # videoDown(baseurl, session)
        t = Thread(target=videoDown, args=(baseurl, session, lock))
        t.start()
        works.append(t)
        # t.join()
    for work in works:
        work.join()
    print('所有下载已完成')


