#!/usr/bin/env python3
"""Generate neon line-art flower SVGs into flowers/svg/ and the gallery flowers/index.html.

usage: python3 tools/gen_flowers.py
"""
import html
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flower_shapes import B, SHAPES  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flowers')
OUT = os.path.join(ROOT, 'svg')

# colour -> (main neon, light accent)
COL = {
    'red': ('#ff3860', '#ffb3c1'), 'crimson': ('#ff2e63', '#ff9db5'),
    'pink': ('#ff7eb6', '#ffd1e6'), 'lightpink': ('#ffb8d6', '#fff0f6'),
    'magenta': ('#ff4fd8', '#ffc1f2'), 'white': ('#f2f6ff', '#ffffff'),
    'yellow': ('#ffe14a', '#fff4b0'), 'orange': ('#ff9a3c', '#ffd4a8'),
    'peach': ('#ffb08a', '#ffe0d0'), 'purple': ('#b48cff', '#e6d6ff'),
    'violet': ('#9a7dff', '#d9ccff'), 'lavender': ('#c9b8ff', '#f1ebff'),
    'blue': ('#5aa9ff', '#c2e0ff'), 'indigo': ('#6f7dff', '#c9ceff'),
    'green': ('#8dffb4', '#e0ffe9'),
}
LEAF = {  # lance leaves for narrow plants, oval leaves for the rest
    'spike': 'lance', 'iris': 'lance', 'lily': 'lance', 'daffodil': 'lance', 'crest': 'lance',
    'bell': 'lance', 'orchid': 'lance',
}

# slug, English, Korean, meaning (en), meaning (ko), shape, kwargs, colour
F = []


def add(*t):
    F.append(t)


# ---- 100 new flowers --------------------------------------------------------
add('lavender', 'Lavender', '라벤더', 'Silence & devotion', '침묵, 기다림', 'spike', {}, 'purple')
add('daffodil', 'Daffodil', '수선화', 'Self-love & respect', '자기애, 존경', 'daffodil', {}, 'yellow')
add('camellia', 'Camellia', '동백', 'Modest beauty', '겸손한 아름다움', 'peony', dict(kind='camellia'), 'crimson')
add('peony', 'Peony', '모란', 'Wealth & honor', '부귀, 영화', 'peony', dict(kind='peony'), 'magenta')
add('rose-of-sharon', 'Rose of Sharon', '무궁화', 'Unchanging devotion', '일편단심', 'trumpet', dict(kind='hibiscus'), 'violet')
add('pansy', 'Pansy', '팬지', 'Think of me', '나를 생각해 주세요', 'pansy', {}, 'purple')
add('chrysanthemum', 'Chrysanthemum', '국화', 'Nobility & truth', '고결, 진실', 'daisy', dict(count=34, length=48, width=5, center=12, layers=2), 'yellow')
add('cosmos', 'Cosmos', '코스모스', 'Innocent love', '순정', 'daisy', dict(count=8, length=56, width=22, center=10, kind='notch'), 'pink')
add('lily', 'Lily', '백합', 'Purity', '순결', 'lily', {}, 'white')
add('freesia', 'Freesia', '프리지아', 'Innocence', '천진난만', 'lily', dict(w=16, l=60), 'yellow')
add('azalea', 'Azalea', '진달래', 'Joy of love', '사랑의 기쁨', 'cherry', dict(notch=False), 'pink')
add('forsythia', 'Forsythia', '개나리', 'Hope', '희망', 'poppy', dict(count=4, w=14, l=64, pointed=True), 'yellow')
add('magnolia', 'Magnolia', '목련', 'Nobility', '고귀함', 'tulip', {}, 'white')
add('lilac', 'Lilac', '라일락', 'First love', '첫사랑', 'hydrangea', dict(florets=19, pr=7, sp=22), 'violet')
add('iris', 'Iris', '아이리스', 'Good news', '기쁜 소식', 'iris', {}, 'purple')
add('carnation', 'Carnation', '카네이션', 'Gratitude & respect', '감사, 존경', 'peony', dict(kind='carnation'), 'red')
add('hydrangea', 'Hydrangea', '수국', 'Sincerity', '진심', 'hydrangea', {}, 'blue')
add('herbaceous-peony', 'Herbaceous Peony', '작약', 'Shyness', '수줍음', 'peony', dict(kind='peony'), 'lightpink')
add('dahlia', 'Dahlia', '달리아', 'Gratitude', '감사', 'peony', dict(kind='dahlia'), 'orange')
add('gerbera', 'Gerbera', '거베라', 'Hope & challenge', '희망, 도전', 'daisy', dict(count=18, length=52, width=9, center=14, layers=2), 'orange')
add('babys-breath', "Baby's Breath", '안개꽃', 'Pure heart', '맑은 마음', 'hydrangea', dict(florets=26, pr=5, scatter=True, seed=3), 'white')
add('forget-me-not', 'Forget-me-not', '물망초', 'Do not forget me', '나를 잊지 마세요', 'cherry', dict(notch=False, l=48, w=26), 'blue')
add('violet', 'Violet', '제비꽃', 'Modesty', '겸양', 'pansy', {}, 'violet')
add('dandelion', 'Dandelion', '민들레', 'Happiness', '행복', 'daisy', dict(count=44, length=50, width=3.5, center=8, dots=False), 'yellow')
add('moss-rose', 'Moss Rose', '채송화', 'Innocence', '순진', 'poppy', dict(count=5, w=34, l=54), 'orange')
add('balsam', 'Balsam', '봉선화', "Don't touch me", '나를 건드리지 마세요', 'orchid', {}, 'pink')
add('cockscomb', 'Cockscomb', '맨드라미', 'Passion', '열정', 'crest', {}, 'red')
add('morning-glory', 'Morning Glory', '나팔꽃', 'Fleeting love', '덧없는 사랑', 'trumpet', dict(kind='glory'), 'indigo')
add('rugosa-rose', 'Rugosa Rose', '해당화', 'Gentleness', '온화', 'poppy', dict(count=5, w=40, l=58), 'pink')
add('royal-azalea', 'Royal Azalea', '철쭉', 'Passion', '열정', 'cherry', dict(notch=False, petals=5, w=32, l=62), 'magenta')
add('plum-blossom', 'Plum Blossom', '매화', 'Nobility & endurance', '고결, 인내', 'cherry', dict(notch=False, w=26, l=52), 'white')
add('apricot-blossom', 'Apricot Blossom', '살구꽃', 'Shyness of a maiden', '처녀의 수줍음', 'cherry', dict(notch=False, w=28, l=56), 'peach')
add('peach-blossom', 'Peach Blossom', '복숭아꽃', 'Captive of love', '사랑의 포로', 'cherry', dict(notch=True, w=26, l=58), 'pink')
add('pear-blossom', 'Pear Blossom', '배꽃', 'Comfort', '위로', 'cherry', dict(notch=False, w=27, l=56), 'white')
add('apple-blossom', 'Apple Blossom', '사과꽃', 'Temptation', '유혹', 'poppy', dict(count=5, w=36, l=56), 'lightpink')
add('acacia', 'Acacia', '아카시아', 'Friendship', '우정', 'spike', dict(kind='delph'), 'white')
add('trumpet-creeper', 'Trumpet Creeper', '능소화', 'Honor', '명예', 'trumpet', dict(kind='glory'), 'orange')
add('crape-myrtle', 'Crape Myrtle', '배롱나무꽃', 'Longing for a lost friend', '떠난 벗을 그리워함', 'cherry', dict(petals=6, notch=True, w=24, l=58), 'magenta')
add('aster-wild', 'Wild Aster', '쑥부쟁이', 'Longing', '그리움', 'daisy', dict(count=22, length=46, width=5, center=12), 'lavender')
add('korean-chrysanthemum', 'Korean Chrysanthemum', '구절초', "Mother's love", '어머니의 사랑', 'daisy', dict(count=16, length=52, width=8, center=14), 'white')
add('rudbeckia', 'Rudbeckia', '루드베키아', 'Eternal happiness', '영원한 행복', 'daisy', dict(count=14, length=44, width=9, center=22, layers=2), 'yellow')
add('echinacea', 'Echinacea', '에키네시아', 'Deep affection', '깊은 애정', 'daisy', dict(count=12, length=46, width=8, center=24), 'magenta')
add('calendula', 'Calendula', '금잔화', 'Sorrow of parting', '이별의 슬픔', 'daisy', dict(count=24, length=42, width=6, center=14, layers=2), 'orange')
add('zinnia', 'Zinnia', '백일홍', 'Bonds', '인연', 'peony', dict(kind='zinnia'), 'red')
add('china-aster', 'China Aster', '과꽃', 'Faithful love', '믿음직한 사랑', 'daisy', dict(count=26, length=44, width=5, center=12, layers=2), 'purple')
add('evening-primrose', 'Evening Primrose', '달맞이꽃', 'Waiting', '기다림', 'poppy', dict(count=4, w=44, l=56), 'yellow')
add('dianthus', 'Dianthus', '패랭이꽃', 'Pure love', '순수한 사랑', 'cherry', dict(notch=True, w=24, l=48), 'pink')
add('shasta-daisy', 'Shasta Daisy', '샤스타데이지', 'Patience', '인내', 'daisy', dict(count=20, length=54, width=7, center=17), 'white')
add('anemone', 'Anemone', '아네모네', 'Anticipation', '기대', 'poppy', dict(count=7, w=30, l=60), 'purple')
add('ranunculus', 'Ranunculus', '라넌큘러스', 'Charm', '매력', 'peony', dict(kind='ranunculus'), 'orange')
add('hyacinth', 'Hyacinth', '히아신스', 'Humble love', '겸손한 사랑', 'spike', dict(kind='stock'), 'blue')
add('crocus', 'Crocus', '크로커스', 'Joy of youth', '청춘의 기쁨', 'tulip', {}, 'violet')
add('snowdrop', 'Snowdrop', '스노드롭', 'Hope', '희망', 'bell', dict(kind='bell', n=3, size=1.5), 'white')
add('primrose', 'Primrose', '프림로즈', 'Eternal love', '영원한 사랑', 'cherry', dict(notch=True, w=30, l=54), 'yellow')
add('delphinium', 'Delphinium', '델피니움', 'I bring you happiness', '행복을 드립니다', 'spike', dict(kind='delph'), 'blue')
add('snapdragon', 'Snapdragon', '금어초', 'Desire', '욕망', 'spike', dict(kind='snap'), 'pink')
add('sweet-pea', 'Sweet Pea', '스위트피', 'Pleasant memories', '즐거운 추억', 'orchid', {}, 'lightpink')
add('stock', 'Stock', '스토크', 'Eternal beauty', '영원한 아름다움', 'spike', dict(kind='stock'), 'pink')
add('lisianthus', 'Lisianthus', '리시안셔스', 'Unchanging love', '변치 않는 사랑', 'trumpet', dict(kind='petunia'), 'lavender')
add('gladiolus', 'Gladiolus', '글라디올러스', 'Passionate love', '정열적 사랑', 'spike', dict(kind='snap'), 'orange')
add('canna', 'Canna', '칸나', 'Respect', '존경', 'iris', {}, 'red')
add('oleander', 'Oleander', '협죽도', 'Caution', '경계', 'cherry', dict(notch=False, w=30, l=60), 'pink')
add('bougainvillea', 'Bougainvillea', '부겐빌레아', 'Passion', '열정', 'poppy', dict(count=3, w=44, l=66), 'magenta')
add('hibiscus', 'Hibiscus', '히비스커스', 'Delicate beauty', '섬세한 아름다움', 'trumpet', dict(kind='hibiscus'), 'red')
add('plumeria', 'Plumeria', '플루메리아', 'Health & hospitality', '건강, 환대', 'poppy', dict(count=5, w=34, l=64), 'white')
add('bird-of-paradise', 'Bird of Paradise', '극락조화', 'Freedom & great journeys', '자유, 멋진 여행', 'orchid', {}, 'orange')
add('anthurium', 'Anthurium', '안스리움', 'Agony of the heart', '번뇌', 'anthurium', {}, 'red')
add('orchid', 'Orchid', '난초', 'Noble character', '고귀한 품격', 'lily', dict(w=11, l=70), 'lavender')
add('phalaenopsis', 'Phalaenopsis', '호접란', 'I love you', '당신을 사랑합니다', 'orchid', {}, 'pink')
add('cyclamen', 'Cyclamen', '시클라멘', 'Shyness', '수줍음', 'poppy', dict(count=5, w=18, l=60, pointed=True), 'pink')
add('poinsettia', 'Poinsettia', '포인세티아', 'Blessing', '축복', 'daisy', dict(count=8, length=70, width=22, center=10, layers=2), 'red')
add('double-cherry', 'Double Cherry Blossom', '겹벚꽃', 'Spiritual love', '정신적 사랑', 'cherry', dict(layers=2, w=30, l=62), 'lightpink')
add('cotton-flower', 'Cotton Flower', '목화', "Mother's love", '어머니의 사랑', 'cherry', dict(notch=False, w=30, l=56), 'white')
add('balloon-flower', 'Balloon Flower', '도라지꽃', 'Eternal love', '영원한 사랑', 'poppy', dict(count=5, w=28, l=62, pointed=True), 'purple')
add('daylily', 'Daylily', '원추리', 'Waiting heart', '기다리는 마음', 'lily', dict(w=24), 'orange')
add('hosta', 'Hosta', '비비추', 'Fate from heaven', '하늘이 내린 인연', 'bell', dict(kind='bell', n=5, size=1.3), 'lavender')
add('pasque-flower', 'Pasque Flower', '할미꽃', 'Sad memories', '슬픈 추억', 'poppy', dict(count=6, w=20, l=60, pointed=True), 'violet')
add('trout-lily', 'Trout Lily', '얼레지', 'Jealousy', '질투', 'lily', dict(w=14, l=66), 'pink')
add('adonis', 'Adonis', '복수초', 'Eternal happiness', '영원한 행복', 'daisy', dict(count=14, length=50, width=10, center=12), 'yellow')
add('bleeding-heart', 'Bleeding Heart', '금낭화', 'I will follow you', '당신을 따르겠습니다', 'bell', dict(kind='heart', n=5, size=1.5), 'pink')
add('cornflower', 'Cornflower', '수레국화', 'Happiness', '행복', 'daisy', dict(count=12, length=44, width=9, center=12, kind='notch'), 'blue')
add('poppy', 'Poppy', '양귀비', 'Consolation', '위로', 'poppy', dict(count=4, w=52, l=66), 'red')
add('gentian', 'Gentian', '용담', 'Justice', '정의', 'tulip', {}, 'blue')
add('lily-of-the-valley', 'Lily of the Valley', '은방울꽃', 'Return of happiness', '반드시 행복해집니다', 'bell', dict(kind='bell', n=6, size=.9), 'white')
add('hellebore', 'Hellebore', '헬레보루스', 'Consolation', '위로', 'cherry', dict(notch=False, w=30, l=58), 'green')
add('clematis', 'Clematis', '클레마티스', 'Spiritual beauty', '정신적 아름다움', 'poppy', dict(count=6, w=28, l=66, pointed=True), 'violet')
add('wisteria', 'Wisteria', '등꽃', 'Welcome', '환영', 'spike', dict(kind='delph'), 'lavender')
add('honeysuckle', 'Honeysuckle', '인동덩굴', 'Devoted love', '헌신적 사랑', 'lily', dict(w=10, l=62), 'yellow')
add('jasmine', 'Jasmine', '재스민', 'Loveliness', '사랑스러움', 'poppy', dict(count=5, w=26, l=60, pointed=True), 'white')
add('gardenia', 'Gardenia', '치자꽃', 'Purity & joy', '청결, 기쁨', 'peony', dict(kind='camellia'), 'white')
add('orange-blossom', 'Orange Blossom', '오렌지꽃', 'Purity & happiness', '순결, 행복', 'poppy', dict(count=5, w=34, l=52), 'white')
add('mimosa', 'Mimosa', '미모사', 'Sensitivity', '민감', 'daisy', dict(count=40, length=36, width=3.5, center=10, dots=False), 'pink')
add('angels-trumpet', "Angel's Trumpet", '엔젤트럼펫', 'Gentle heart', '부드러운 마음', 'bell', dict(kind='bell', n=3, size=1.7), 'peach')
add('hollyhock', 'Hollyhock', '접시꽃', 'Abundance', '풍요', 'trumpet', dict(kind='hibiscus'), 'pink')
add('nasturtium', 'Nasturtium', '한련화', 'Patriotism', '애국심', 'trumpet', dict(kind='hibiscus'), 'orange')
add('petunia', 'Petunia', '페튜니아', "I feel at ease with you", '당신과 함께라면 마음이 편안해요', 'trumpet', dict(kind='petunia'), 'magenta')
add('begonia', 'Begonia', '베고니아', 'Unrequited love', '짝사랑', 'poppy', dict(count=4, w=36, l=52), 'pink')
add('geranium', 'Geranium', '제라늄', 'Unwavering trust', '변치 않는 신뢰', 'hydrangea', dict(florets=7, pr=15, sp=34), 'red')
add('spirea', 'Spirea', '설유화', 'Charm', '애교', 'hydrangea', dict(florets=19, pr=6, sp=24), 'white')
add('poinsettia-pink', 'Christmas Star', '꽃기린', 'Love through hardship', '고난의 사랑', 'cherry', dict(notch=False, w=22, l=44), 'red')

# ---- colour variants of the six flowers from the reference video ---------------
add('rose-red', 'Red Rose', '빨간 장미', 'Passionate love', '열렬한 사랑', 'rose', {}, 'red')
add('rose-pink', 'Pink Rose', '분홍 장미', 'Gratitude & happy love', '감사, 행복한 사랑', 'rose', {}, 'pink')
add('rose-white', 'White Rose', '흰 장미', 'Purity & respect', '순결, 존경', 'rose', {}, 'white')
add('rose-yellow', 'Yellow Rose', '노란 장미', 'Friendship & jealousy', '우정, 질투', 'rose', {}, 'yellow')
add('rose-purple', 'Purple Rose', '보라 장미', 'Enchantment & eternal love', '신비, 영원한 사랑', 'rose', {}, 'purple')
add('tulip-red', 'Red Tulip', '빨간 튤립', 'Declaration of love', '사랑의 고백', 'tulip', {}, 'red')
add('tulip-yellow', 'Yellow Tulip', '노란 튤립', 'Hopeless love', '헛된 사랑', 'tulip', {}, 'yellow')
add('tulip-white', 'White Tulip', '흰 튤립', 'Forgiveness & new start', '용서, 새 출발', 'tulip', {}, 'white')
add('tulip-purple', 'Purple Tulip', '보라 튤립', 'Eternal love', '영원한 사랑', 'tulip', {}, 'purple')
add('tulip-pink', 'Pink Tulip', '분홍 튤립', 'Caring & affection', '배려, 애정', 'tulip', {}, 'pink')
add('sunflower-yellow', 'Sunflower', '해바라기', 'Unwavering devotion', '변치 않는 숭배', 'daisy', dict(count=26, length=34, width=10, center=34, layers=2), 'yellow')
add('sunflower-orange', 'Orange Sunflower', '주황 해바라기', 'Warmth & energy', '따뜻함, 활력', 'daisy', dict(count=26, length=34, width=10, center=34, layers=2), 'orange')
add('cherry-pink', 'Cherry Blossom', '벚꽃', 'The beauty of life', '삶의 아름다움', 'cherry', {}, 'pink')
add('cherry-white', 'White Cherry Blossom', '흰 벚꽃', 'Purity & innocence', '순수, 순결', 'cherry', {}, 'white')
add('lotus-pink', 'Pink Lotus', '분홍 연꽃', 'Purity of heart', '마음의 순수', 'lotus', {}, 'lavender')
add('lotus-white', 'White Lotus', '흰 연꽃', 'Enlightenment', '깨달음', 'lotus', {}, 'white')
add('lotus-blue', 'Blue Lotus', '파란 연꽃', 'Wisdom', '지혜', 'lotus', {}, 'blue')
add('daisy-white', 'Daisy', '데이지', 'Peace and hope', '평화, 희망', 'daisy', dict(count=26, length=54, width=6, center=16), 'white')
add('daisy-pink', 'Pink Daisy', '분홍 데이지', 'Sweet innocence', '순수한 사랑', 'daisy', dict(count=26, length=54, width=6, center=16), 'pink')
add('daisy-yellow', 'Yellow Daisy', '노랑 데이지', 'Cheerfulness', '명랑함', 'daisy', dict(count=26, length=54, width=6, center=16), 'yellow')
add('daisy-blue', 'Blue Daisy', '파랑 데이지', 'Trust & loyalty', '신뢰, 충실', 'daisy', dict(count=26, length=54, width=6, center=16), 'blue')

HEAD = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600" style="--c:{c};--c2:{c2}">
<title>{en} - neon line art</title>
<defs>
<radialGradient id="bg" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#14183a"/><stop offset="1" stop-color="#080a1a"/></radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.d{{fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1;animation:draw var(--t,1s) ease-out var(--s,0s) forwards}}
.stem{{stroke:#3df2c0;stroke-width:3}}
.pet{{stroke:var(--c);stroke-width:2}}
.pet2{{stroke:var(--c2);stroke-width:1.6}}
.rip{{stroke:#5ad7ff;stroke-width:2.4}}
.fi{{opacity:0;animation:fade .5s ease-out var(--s,0s) forwards}}
.dotc{{fill:var(--c2)}}
.title{{font-family:'Poppins','Helvetica Neue',Arial,sans-serif;font-weight:600;fill:none;stroke:var(--c);stroke-width:1.6;opacity:0;animation:fade 1s ease-out var(--s) forwards}}
.sub{{font-family:'Poppins','Helvetica Neue',Arial,sans-serif;font-weight:500;fill:var(--c2);opacity:0;animation:fade 1s ease-out calc(var(--s) + .6s) forwards}}
.ko{{font-family:'Noto Sans KR','Malgun Gothic','Apple SD Gothic Neo',sans-serif;fill:#aab0d6;opacity:0;animation:fade 1s ease-out calc(var(--s) + 1.1s) forwards}}
.sp{{fill:var(--c2);opacity:0;animation:tw 3s ease-in-out infinite}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes tw{{0%,100%{{opacity:0;transform:translateY(0)}}50%{{opacity:.9;transform:translateY(-14px)}}}}
</style>
</defs>
<rect width="800" height="600" fill="url(#bg)"/>
<g filter="url(#glow)">'''


def leaves(style):
    L = B(0)
    if style == 'lance':
        L.p("M229 540 C190 500 160 440 150 380 C190 410 225 470 229 540", 'stem', at=1.5, dur=1)
        L.p("M231 520 C270 480 300 420 312 360 C268 395 235 455 231 520", 'stem', at=1.7, dur=1)
        L.p("M230 470 C205 440 195 400 192 360", 'stem', at=1.9, dur=.8)
    else:
        L.p("M230 480 C190 495 158 465 152 425 C192 422 226 440 230 480Z", 'stem', at=1.4, dur=1)
        L.p("M230 440 C268 452 300 425 306 388 C266 388 234 404 230 440Z", 'stem', at=1.7, dur=1)
    return L.out()


def render(slug, en, ko, men, mko, shape, kw, color):
    c, c2 = COL[color]
    b = B(2.0)
    meta = SHAPES[shape](b, **kw)
    hy, tx = meta.get('hy', 190), meta.get('tx', 230)
    sc = {'spike': 1.0, 'bell': 1.0, 'lotus': 1.3}.get(shape, 1.2)
    parts = [HEAD.format(c=c, c2=c2, en=html.escape(en))]
    top = meta.get('top')
    if top is not None:
        yt = hy + top * sc
        m1 = 560 - (560 - yt) * .35
        m2 = 560 - (560 - yt) * .7
        s = B(0)
        s.p(f"M230 560 C226 {m1:.0f} 234 {m2:.0f} 230 {yt:.0f}", 'stem', at=0, dur=2)
        parts.append(s.out())
    if meta.get('leaves', True):
        parts.append(leaves(LEAF.get(shape, 'oval')))
    parts.append(meta.get('extra', ''))
    parts.append(f'<g transform="translate({tx} {hy}) scale({sc})">{b.out()}</g></g>')
    t = max(b.t + .3, 3.4)
    t = min(t, 6.5)
    size = min(54, 410 / (.68 * len(en)))
    msize = min(22, 430 / (.55 * len(men)))
    parts.append(f'<text class="title" x="360" y="270" font-size="{size:.0f}" style="--s:{t:.1f}s">{html.escape(en)}</text>')
    parts.append(f'<text class="sub" x="364" y="315" font-size="{msize:.0f}" style="--s:{t:.1f}s">{html.escape(men)}</text>')
    ksize = min(20, 400 / max(len(ko) + len(mko) + 3, 1) * 1.6)
    parts.append(f'<text class="ko" x="364" y="352" font-size="{ksize:.0f}" style="--s:{t:.1f}s">{html.escape(ko)} · {html.escape(mko)}</text>')
    rnd = random.Random(slug)
    for i in range(7):
        parts.append(f'<circle class="sp" cx="{rnd.randint(60, 760)}" cy="{rnd.randint(80, 540)}" r="{rnd.choice([1.5, 2, 2.5])}" '
                     f'style="animation-delay:{i * .5:.1f}s"/>')
    parts.append('</svg>')
    return '\n'.join(parts)


def gallery():
    cards = ''.join(
        f'<figure><img loading="lazy" src="svg/{s}.svg" alt="{html.escape(en)}"><figcaption><b>{html.escape(en)}</b>'
        f'<span>{html.escape(ko)} · {html.escape(mko)}</span></figcaption></figure>'
        for s, en, ko, men, mko, *_ in F)
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Neon Flowers</title>
<style>
:root{{--bg:#080a1a;--fg:#e6e9ff;--mut:#8f95c4}}
body{{margin:0;padding:24px 16px;background:var(--bg);color:var(--fg);font-family:'Noto Sans KR','Malgun Gothic',system-ui,sans-serif}}
h1{{text-align:center;font-weight:600}}p.n{{text-align:center;color:var(--mut)}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;max-width:1400px;margin:24px auto}}
figure{{margin:0;background:#0d1030;border-radius:12px;overflow:hidden}}
img{{width:100%;display:block}}
figcaption{{padding:10px 12px;display:flex;flex-direction:column;gap:2px;font-size:14px}}figcaption span{{color:var(--mut);font-size:12px}}
</style></head><body>
<h1>Neon Flowers · {len(F)}</h1><p class="n">flowers/svg/*.svg — 클릭 없이 열면 바로 애니메이션이 재생됩니다</p>
<div class="g">{cards}</div></body></html>'''


def main():
    os.makedirs(OUT, exist_ok=True)
    slugs = [f[0] for f in F]
    assert len(slugs) == len(set(slugs)), 'duplicate slug'
    only = set(sys.argv[1:])
    for f in F:
        if only and f[0] not in only:
            continue
        with open(os.path.join(OUT, f[0] + '.svg'), 'w', encoding='utf-8') as fh:
            fh.write(render(*f))
    with open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8') as fh:
        fh.write(gallery())
    print(len(F), 'flowers')


if __name__ == '__main__':
    main()
