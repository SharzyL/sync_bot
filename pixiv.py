import os
import re
from concurrent.futures import ThreadPoolExecutor
from os.path import join
from time import sleep

import requests

import bot
from log import *

IMG_dir = 'pixiv'
if not os.path.exists(IMG_dir):
    os.makedirs(IMG_dir)
HEADER = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8,zh-TW;q=0.7',
    'cache-control': 'no-cache',
    'cookie': 'first_visit_datetime_pc=2019-04-05+01%3A42%3A14; p_ab_id=7; p_ab_id_2=6; p_ab_d_id=1206298427; yuid_b=GDQYJFA; privacy_policy_agreement=1; c_type=21; a_type=0; b_type=1; tag_view_ranking=RTJMXD26Ak~Lt-oEicbBr~jH0uD88V6F~LJo91uBPz4~pzzjRSV6ZO~PTyxATIsK0~65aiw_5Y72~eVxus64GZU~faHcYIP1U0~tgP8r-gOe_~ixJ21_XZkb~b1s-xqez0Y~kMjNs0GHNN~j-qKQjHtZA~D0s_SuPaI-~gpglyfLkWs~1Xn1rApx2-~SyW_eeu1fJ~QY0E__NxQs~zCFlzyuz7F~BAlznzbb3b~2XjntDOwrr~noyKIE4uzj~EUwzYuPRbU~HFX-xbTwCV~-StjcwdYwv~rELYgW0qN3~RybylJRnhJ~MhieHQxNXo~q3eUobDMJW~BU9SQkS-zU~y8GNntYHsi~7YjK_c_EhV~lRdaFwhKcW~P-jVO8CNUe~UNCAZrooFv~HY55MqmzzQ~NpsIVvS-GF~Isimpx6lUN~gE1I1uL-Uu~bElhJJX2Jc~xGbDuPIiod~Itu6dbmwxu~LtW-gO6CmS~qNNBETb79P~NqREve0QPf~kzV9AbHIzz~562khdE7He~BDaS_dJLHi~38QHnJb19N~gCByqxH2wJ~nRp2ZLPLbj; module_orders_mypage=%5B%7B%22name%22%3A%22sketch_live%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22tag_follow%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22recommended_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22everyone_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22following_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22mypixiv_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22spotlight%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22fanbox%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22featured_tags%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22contests%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22user_events%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22sensei_courses%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22booth_follow_items%22%2C%22visible%22%3Atrue%7D%5D; login_ever=yes; login_bc=1; PHPSESSID=11980598_77529f9c28b0ecba1f84167b256316a1; device_token=4975a91d2df86ecf39a0f8e37f2b3f0f',
    'dnt': '1',
    'pragma': 'no-cache',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
}
logger = get_logger('pixiv_spider')

print('')


class PixivImg:
    def __init__(self, work, cnt=0):
        """
        :param work: a dict, with following keys: id, title, url, tag [], pagecount, etc
        :param cnt: a counter to record in filename (oldest 0, the newer, the bigger)
        """
        self.cnt = cnt
        self.id = work['id']
        self.title = work['title']
        self.type = work['illustType']
        self.tags = work['tags']
        date = re.findall(r'(?<=img)(?:/\d{2,4})+(?=/)', work['url'])[0]  # date is a string like '/2017/02/16/17/56/25'
        self.page_cnt = work['pageCount']
        self.img_urls_no_suffix = [
            f'https://i.pximg.net/img-original/img{date}/{self.id}_p{i}'
            for i in range(self.page_cnt)]

    def __repr__(self):
        return f'<PixivImg object id: {self.id} name: {self.title}'

    @log_func(logger)
    def get(self):
        if self.type == 2:
            logger.info('Downloading gif is not implemented yet')
            return
        suffixes = ['.png', '.jpg']
        referer = f'https://www.pixiv.net/member_illust.php?mode=medium&illust_id={self.id}'
        for i, url in enumerate(self.img_urls_no_suffix):
            header = HEADER.copy()
            header['Referer'] = referer
            r, suffix = None, None
            for suffix in suffixes:
                r = requests.get(url + suffix, headers=header, proxies=bot.PROXY)
                if r.status_code == 403 or r.status_code == 404:
                    continue
                else:
                    break
            else:
                raise ConnectionError('Cannot get image (maybe it is a GIF)')
            filename = f'{self.cnt:0>4}_{self.id}_p{i}{suffix}'
            with open(join(IMG_dir, filename), 'wb') as fp:
                fp.write(r.content)


def get_collections(uid: int):
    url = f'https://www.pixiv.net/ajax/user/{uid}/illusts/bookmarks?tag=&offset=0&limit=100000&rest=show'
    req = requests.get(url, headers=HEADER).json()
    if req['error']:
        raise ConnectionError('Invalid request', url)
    works = req['body']['works']
    length = len(works)
    logger.info('Get %s image info', length)
    return [PixivImg(work, length - i) for i, work in enumerate(works)]


def sync_to_local(uid):
    imgs = get_collections(uid)
    executor = ThreadPoolExecutor(max_workers=10)
    img_id_regex = re.compile(r'(?:^\d+)_(\d+)')
    saved_files = {int(img_id_regex.findall(filename)[0]) for filename in os.listdir(IMG_dir)}
    for img in imgs:
        if int(img.id) in saved_files:
            continue
        executor.submit(PixivImg.get, img)
        sleep(5)


if __name__ == '__main__':
    sync_to_local(11980598)
