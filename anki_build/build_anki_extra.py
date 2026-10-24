#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""翻译语料精选 Anki 卡片构建脚本。

数据源：内嵌 PAIRS（116 条中英对照语料，用户提供）
产物：CET4翻译_语料.apkg
  牌组 CET4 翻译::04 汉英翻译语料（双向卡片，中→英 / 英→中）

约定与 build_anki.py 保持一致：
  - 复用其 CSS 与 clean_zh（去掉正面括注的英文提示）
  - guid 方案 genanki.guid_for("cet4tr", ...)
  - 小瑕疵条目：原译文保留在「英文」字段，更地道译法放入「备注」，
    仅出现在「中→英」答案面，不替换原译文

用法：python3 build_anki_extra.py
"""
import os
import sys
import html

# genanki 装在 user site-packages，脚本可能以 -I 启动
sys.path.insert(0, os.path.expanduser("~/.local/lib/python3.14/site-packages"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genanki  # noqa: E402
from build_anki import CSS, clean_zh  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

DECK_NAME = "CET4 翻译::04 汉英翻译语料"
TAG_ROOT = "CET4::翻译::语料"

# (中文, 英文, 备注)  —— 备注仅 4 条小瑕疵条目，放更地道译法
PAIRS = [
    ("中国是文明古国，拥有悠久历史。", "China is an ancient civilization with a long history.", ""),
    ("爆竹（firecrackers）是中国传统文化中的重要元素之一。它在中国有悠久的历史。",
     "Firecrackers are one of the important elements in Chinese traditional culture. They have a long history in China.", ""),
    ("重庆是一座山城，备受游客喜爱。", "Chongqing is a mountain city, and it is loved by many tourists.", ""),
    ("我是一名大学生，主修人文学科。", "I am a college student, majoring in humanities.", ""),
    ("中国文化的一个重要元素", "an important element of Chinese culture", ""),
    ("环保意识的增强", "the increase in environmental awareness", ""),
    ("爆竹的使用", "the use of firecrackers", ""),
    ("悠久的历史", "a long history", ""),
    ("灿烂美丽的文化", "a bright and beautiful culture", "更地道：a splendid / brilliant and beautiful culture"),
    ("高度发达的产业", "highly developed industries", ""),
    ("受人们喜爱的小说人物", "a novel character loved by people", ""),
    ("获得财富的小男孩", "the little boy who gained wealth", "更地道：the little boy who made his fortune"),
    ("收到礼物的小朋友", "the child who received the gift", ""),
    ("被父母批评的孩子", "the child criticized by his parents", ""),
    ("有着花园的房子", "the house with a garden", ""),
    ("对婚姻有着偏见的人们", "people who have a prejudice against marriage", ""),
    ("中国有 14 亿人口。", "China has a population of 1.4 billion.", ""),
    ("唐代诗人有许多著作。", "Tang Dynasty poets wrote many works.", ""),
    ("在美国，有高度发达的芯片技术。", "In the United States, there is highly developed chip technology.", ""),
    ("2008 年有一场地震。", "There was an earthquake in 2008.", ""),
    ("他是一名著名的主持人，有着很多粉丝。", "He is a famous host with many fans.", ""),
    ("中国十分重视环境保护，有许多相关的政策。", "China attaches great importance to environmental protection and has many related policies.", ""),
    ("随着环保意识的增强", "With the increase in environmental awareness,", ""),
    ("随着人们兴趣的增加", "With the increase in people's interest,", ""),
    ("随着收入的减少", "With the decrease in income,", ""),
    ("随着人们对中国传统文化越来越感兴趣", "As people become more and more interested in traditional Chinese culture,", ""),
    ("随着当地政府开始重视人们的生活质量", "As the local government began to pay attention to people's quality of life,", ""),
    ("重庆大学是众多高等院校之一。", "Chongqing University is one of the many institutions of higher learning.", ""),
    ("国画是中国文化艺术种类之一。", "Chinese painting is one of the forms of Chinese culture and art.", ""),
    ("中国传统文化中的重要元素之一。", "One of the important elements in traditional Chinese culture.", ""),
    ("中国幅员辽阔，人口众多。", "China has a vast territory and a large population.", ""),
    ("这部电影粉丝很多，口碑很好。", "This movie has many fans and a good reputation.", ""),
    ("人们认为，通过这么做，可以驱散厄运，带来好运吉祥。", "People believe that by doing so, one can drive away bad luck and bring good luck.", ""),
    ("战后改变了世界格局。", "After the war, the world order changed.", ""),
    ("通过政府引导和社会参与，建立更多的养老机构。", "More elderly care institutions should be set up through government guidance and social participation.", ""),
    ("灯笼内部点燃蜡烛。", "A candle is lit inside the lantern.", ""),
    ("农业生产活动", "agricultural production activities", ""),
    ("经济文化社会发展", "economic, cultural and social development", ""),
    ("社会实践活动", "social practice activities", ""),
    ("中国传统绘画历史十分悠久。", "Traditional Chinese painting has a very long history.", ""),
    ("唐代，经济繁荣，人们生活幸福，进出口产业发达。",
     "During the Tang Dynasty, the economy was prosperous, people lived a happy life, and the import and export industry was well developed.", ""),
    ("1999 年，世界经历了巨大变化。", "In 1999, the world experienced great changes.", ""),
    ("在古代，人们崇尚尊师重道。", "In ancient times, people respected teachers and valued moral principles.", ""),
    ("他已经被说服去洗碗了。", "He has been persuaded to wash the dishes.", ""),
    ("中国一直践行绿色发展的方针。", "China has always followed the policy of green development.", ""),
    ("自 2000 年以来，中国驶入经济发展快车道。", "Since 2000, China has entered a period of rapid economic development.", ""),
    ("在过去 20 年里，他饱经沧桑，阅人无数，深谙人生之道。",
     "In the past 20 years, he has gone through many hardships, met all kinds of people, and gained a deep understanding of life.", ""),
    ("铁观音一年四季均可采摘。", "Tieguanyin can be picked in all four seasons of the year.", ""),
    ("粮食一般在春天种植，秋天收获，冬天储存。", "Crops are generally planted in spring, harvested in autumn, and stored in winter.", ""),
    ("你的行程确定后，一定要告诉我。", "After your trip is confirmed, be sure to tell me.", ""),
    ("新规则制定后，大家一定要遵守。", "After the new rules are made, everyone must obey them.", ""),
    ("他飞越了大半个地球，去到了梦想中的地方。", "He flew across most of the earth and reached the place of his dreams.", ""),
    ("她接听了电话，变得十分沮丧。", "She answered the phone and became very upset.", ""),
    ("熊猫是十分可爱的动物，深受世界各地的人们喜爱。", "Pandas are very lovely animals and are loved by people all over the world.", ""),
    ("他们跟你建立了深厚的感情，不希望你离开。", "They have formed a deep bond with you and don't want you to leave.", ""),
    ("我喜欢这枚闪闪发光的戒指，它真的很漂亮。", "I like this shining ring, and it is really beautiful.",
     "更地道：I like this sparkling ring, and it is really beautiful."),
    ("人总是不愿意遵守规则，规则最终也被人们打破。", "People are always unwilling to obey the rules, and in the end the rules are broken by them.", ""),
    ("中国有很多艺术家，他们十分有才华。", "There are many artists in China, and they are very talented.", ""),
    ("中国有很多艺术家，他们中的大部分有才华。", "China has many artists, and most of them are talented.", ""),
    ("他从不吃他讨厌的食物。", "He never eats the food that he dislikes.", ""),
    ("Jacky 从来不听别人指出的缺点。", "Jacky never listens to the shortcomings pointed out by others.", ""),
    ("你应该多锻炼，这对你很重要。", "You should exercise more, and it is very important to you.", ""),
    ("凡人多舛误，唯神能见宥，这是十分正确的。", "Humans often make mistakes, and only God can forgive them. This is quite true.", ""),
    ("中国坚持在保护环境中发展，在发展中保护环境，这获得了大多数国家的认可。",
     "China insists on developing while protecting the environment, and protecting the environment while developing. This has been recognized by most countries.",
     "更地道：…protecting the environment while developing, and vice versa"),
    ("中国古代的人们道德水平很高。", "Ancient Chinese people had high moral standards.", ""),
    ("张军在大数据方面表现十分优秀。", "Zhang Jun performs very well in big data.", ""),
    ("它在众多中小型企业中不算突出。", "It is not outstanding among the many small and medium-sized enterprises.", ""),
    ("在中国，很多人在互联网上当键盘侠。", "In China, many people are keyboard warriors on the Internet.", ""),
    ("你可以通过互联网获得很多信息。", "You can get a lot of information through the Internet.", ""),
    ("科学家根据自然界的规律发明了很多科技。", "Scientists have invented many technologies according to the laws of nature.", ""),
    ("宋代出现了火药爆竹。", "Gunpowder firecrackers appeared in the Song Dynasty.", ""),
    ("2030 年发生了断网停电。", "In 2030, the internet stopped working and the power went out.", ""),
    ("这片区域存在很多资源。", "There are many resources in this area.", ""),
    ("中国的房价之所以一路飙升与购房观念息息相关。",
     "The reason why house prices in China have kept rising is closely related to people's ideas about buying houses.", ""),
    ("一年四季的变化。", "the changes of the four seasons", ""),
    ("南京长江大桥是中国设计、采用国产材料建造的铁路、公路两用桥。",
     "The Nanjing Yangtze River Bridge is a railway and highway bridge which was designed by China and built with domestic materials.", ""),
    ("我们要彻底解决缺水、营养不良的难题。", "We must completely solve the problems of water shortage and malnutrition.", ""),
    ("我们要坚持“人民至上”的方针。", 'We must stick to the policy of "putting people first".', ""),
    ("它们彼此之间相互关联。", "They are related to each other.", ""),
    ("推行家庭养老和社会养老相结合的模式。", "We should adopt a model that combines family care for the elderly with social care for the elderly.", ""),
    ("归属感", "sense of belonging", ""),
    ("飞跃", "leap forward", ""),
    ("总部", "headquarters", ""),
    ("通道", "passage", ""),
    ("羊圈", "sheep pen", ""),
    ("房子成为中国人有归属感的重要标志，并深入人心。",
     "A house has become an important symbol of belonging for Chinese people, and it is deeply rooted in their hearts.", ""),
    ("中国桥梁建设的一个飞跃。", "A leap in China's bridge construction.", ""),
    ("中央电视台总部设有一条穿过大楼的专用通道。", "CCTV headquarters has a special passage that goes through the building.", ""),
    ("夜间有狼钻进了羊圈（sheepfold）叼走了羊。", "At night, a wolf got into the sheepfold and carried off a sheep.", ""),
    ("300 名游客", "300 tourists", ""),
    ("三千名游客", "three thousand tourists", ""),
    ("三万名游客", "thirty thousand tourists", ""),
    ("三十万名游客", "300,000 tourists", ""),
    ("三十三万名游客", "330,000 tourists", ""),
    ("两百万名游客", "2 million tourists", ""),
    ("两千万名游客", "20 million tourists", ""),
    ("两千三百万名游客", "23 million tourists", ""),
    ("1 亿游客", "100 million tourists", ""),
    ("55 亿游客", "5.5 billion tourists", ""),
    ("你需要抽出你四分之三的时间。", "You need to set aside three quarters of your time.", ""),
    ("给我一半的钱。", "Give me half of the money.", ""),
    ("唐朝", "the Tang Dynasty", ""),
    ("宋朝", "the Song Dynasty", ""),
    ("元朝", "the Yuan Dynasty", ""),
    ("唐宋时期", "the Tang and Song dynasties", ""),
    ("春秋时期", "the Spring and Autumn Period", ""),
    ("公元 2009 年", "In 2009 AD", ""),
    ("春节", "the Spring Festival", ""),
    ("元宵节", "the Lantern Festival", ""),
    ("2010 年", "2010", ""),
    ("长江", "the Yangtze River", ""),
    ("黄河", "the Yellow River", ""),
    ("珠江", "the Pearl River", ""),
    ("黄山", "Mount Huang", ""),
    ("太湖", "Lake Tai", ""),
    ("渤海", "the Bohai Sea", ""),
]

# ---------------------------------------------------------------- 笔记类型

MODEL_EXTRA = genanki.Model(
    1751002002,
    "CET4_翻译·语料",
    fields=[{"name": n} for n in ("中文", "英文", "备注")],
    templates=[
        {
            "name": "中 → 英",
            "qfmt": '<div class="wrap"><div class="zh">{{中文}}</div></div>',
            "afmt": ('<div class="wrap"><div class="zh">{{中文}}</div>'
                     '<hr id="answer"><div class="en">{{英文}}</div>'
                     '{{#备注}}<div class="footnote">{{备注}}</div>{{/备注}}</div>'),
        },
        {
            "name": "英 → 中",
            "qfmt": '<div class="wrap"><div class="en">{{英文}}</div></div>',
            "afmt": ('<div class="wrap"><div class="en">{{英文}}</div>'
                     '<hr id="answer"><div class="zh">{{中文}}</div></div>'),
        },
    ],
    css=CSS,
)


def esc(s):
    return html.escape(s, quote=False).strip()


DECK_ID = 1751002001


def build_notes():
    """-> [(牌组名, Note)]，供 build_all.py 合并构建复用。"""
    notes = []
    seen = set()
    for zh, en, note in PAIRS:
        zh_c = esc(clean_zh(zh))
        g = genanki.guid_for("cet4tr", "语料", zh_c)
        if g in seen:
            print("  ! 重复条目已跳过:", zh_c, file=sys.stderr)
            continue
        seen.add(g)
        notes.append((DECK_NAME, genanki.Note(
            model=MODEL_EXTRA,
            fields=[zh_c, esc(en), esc(note)],
            tags=[TAG_ROOT],
            guid=g,
        )))
    return notes


def main():
    deck = genanki.Deck(DECK_ID, DECK_NAME)
    for _, note in build_notes():
        deck.add_note(note)

    outpath = os.path.join(HERE, "CET4翻译_语料.apkg")
    genanki.Package(deck).write_to_file(outpath)

    n = len(deck.notes)
    print(f"牌组 {DECK_NAME}")
    print(f"笔记 {n} 条，卡片 {n * 2} 张（中→英 / 英→中 各 {n}）")
    print(f"带备注（更地道译法）{sum(1 for _, _, x in PAIRS if x)} 条")
    print("已写出", outpath)


if __name__ == "__main__":
    main()
