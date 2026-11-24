"""Reusable, text-free vector illustrations for story videos."""

from __future__ import annotations


ILLUSTRATIONS = {
    "parcel_route": "Đường đi của kiện hàng",
    "rainy_street": "Đường phố trời mưa",
    "idea_lab": "Ý tưởng và nghiên cứu",
    "calendar_clock": "Lịch và thời gian",
    "team_talk": "Hai người trao đổi",
    "growth_steps": "Tiến bộ từng bước",
    "data_network": "Mạng dữ liệu kết nối",
    "balance_scale": "Cân nhắc hai lựa chọn",
    "wallet_payment": "Thanh toán và ví tiền",
    "search_document": "Tìm thông tin trong tài liệu",
    "secure_lock": "Khóa bảo vệ dữ liệu",
    "storyboard": "Khung hình dựng video",
}


def svg(name: str, progress: float = 1.0) -> str:
    if name not in ILLUSTRATIONS:
        raise ValueError(f"Unknown illustration: {name}")
    p = max(0.0, min(1.0, float(progress)))
    blue, teal, orange, ink = "#426db8", "#168e8a", "#e88942", "#20354b"
    base = ['<svg xmlns="http://www.w3.org/2000/svg" width="520" height="300" viewBox="0 0 520 300">',
            '<rect x="8" y="8" width="504" height="284" rx="25" fill="#edf4f8"/>',
            '<circle cx="439" cy="61" r="64" fill="#dfeef2" opacity=".7"/>']
    if name == "parcel_route":
        base += [f'<path d="M91 211 C144 218 143 96 257 137 S370 243 437 87" fill="none" stroke="{blue}" stroke-width="8" stroke-linecap="round" stroke-dasharray="12 13" opacity="{p:.2f}"/>',
                 f'<g opacity="{min(1,p*2):.2f}"><path d="M88 202C44 157 53 100 88 100s44 57 0 102Z" fill="{orange}"/><circle cx="88" cy="133" r="16" fill="white"/></g>',
                 f'<g opacity="{min(1,max(0,(p-.3)*2)):.2f}"><path d="M431 123c-44-45-35-102 0-102s44 57 0 102Z" fill="{teal}"/><circle cx="431" cy="54" r="16" fill="white"/></g>',
                 f'<g opacity="{min(1,max(0,(p-.55)*2.5)):.2f}"><rect x="207" y="175" width="100" height="82" rx="8" fill="#dcae72" stroke="{ink}" stroke-width="5"/><path d="M207 176l50 29 50-29M257 205v52" fill="none" stroke="{ink}" stroke-width="4"/></g>']
    elif name == "rainy_street":
        base += [f'<rect x="54" y="122" width="160" height="130" rx="10" fill="#d8e9f1" stroke="{blue}" stroke-width="5"/>',
                 f'<rect x="74" y="143" width="50" height="58" rx="5" fill="white"/><rect x="145" y="143" width="50" height="58" rx="5" fill="white"/>',
                 f'<path d="M45 127h178" stroke="{orange}" stroke-width="15" stroke-linecap="round"/>',
                 f'<path d="M303 199Q354 91 416 199" fill="{teal}"/><path d="M359 191v54q0 20 24 10" fill="none" stroke="{ink}" stroke-width="6" stroke-linecap="round"/>',
                 '<path d="M42 263h435" stroke="#9cb7c8" stroke-width="5"/>']
        for i in range(9):
            x = 55 + i * 48
            y = 48 + ((i * 31 + int(p * 80)) % 92)
            base.append(f'<path d="M{x} {y}l-10 21" stroke="#6faace" stroke-width="4" stroke-linecap="round" opacity="{.4+.6*p:.2f}"/>')
    elif name == "idea_lab":
        base += [f'<circle cx="180" cy="125" r="67" fill="#fce6a3" stroke="{orange}" stroke-width="5" opacity="{.4+.6*p:.2f}"/>',
                 f'<path d="M149 136q-37-30-16-67 18-29 49-29 36 0 53 29 21 36-14 68l-10 23h-51Z" fill="#fff7d6" stroke="{ink}" stroke-width="6"/>',
                 f'<path d="M159 170h54m-48 17h42" stroke="{ink}" stroke-width="6" stroke-linecap="round"/>',
                 f'<path d="M298 89h145v139H298z" fill="white" stroke="{blue}" stroke-width="5"/>',
                 f'<path d="M317 121h91m-91 28h108m-108 28h76" stroke="#9bb4ca" stroke-width="6" stroke-linecap="round"/>',
                 f'<circle cx="420" cy="202" r="20" fill="{teal}" opacity="{p:.2f}"/>']
        for x,y in ((88,70),(273,62),(81,153),(278,151)):
            base.append(f'<path d="M{x-8} {y}h16M{x} {y-8}v16" stroke="{orange}" stroke-width="4" stroke-linecap="round" opacity="{p:.2f}"/>')
    elif name == "calendar_clock":
        base += [f'<rect x="55" y="69" width="220" height="178" rx="16" fill="white" stroke="{blue}" stroke-width="6"/>',
                 f'<path d="M55 108h220" stroke="{blue}" stroke-width="13"/>',
                 f'<path d="M105 53v31m121-31v31" stroke="{ink}" stroke-width="8" stroke-linecap="round"/>']
        for row in range(2):
            for col in range(3):
                x,y=96+col*65,146+row*47
                base.append(f'<rect x="{x}" y="{y}" width="29" height="23" rx="5" fill="{orange if row==1 and col==1 else "#d9e7ef"}" opacity="{min(1,p*2):.2f}"/>')
        base += [f'<circle cx="379" cy="157" r="87" fill="white" stroke="{teal}" stroke-width="7"/>',
                 f'<path d="M379 94v13m0 100v13m-63-63h13m100 0h13" stroke="{ink}" stroke-width="5"/>',
                 f'<path d="M379 157v-49m0 49l{38*p:.1f} {27*p:.1f}" stroke="{orange}" stroke-width="8" stroke-linecap="round"/>',
                 f'<circle cx="379" cy="157" r="8" fill="{ink}"/>']
    elif name == "team_talk":
        base += [f'<circle cx="157" cy="180" r="35" fill="white" stroke="{ink}" stroke-width="5"/>',
                 f'<circle cx="365" cy="180" r="35" fill="white" stroke="{ink}" stroke-width="5"/>',
                 f'<path d="M86 258q14-47 71-47t71 47M294 258q14-47 71-47t71 47" fill="none" stroke="{blue}" stroke-width="8" stroke-linecap="round"/>',
                 f'<path d="M55 53h180q20 0 20 20v43q0 20-20 20h-64l-18 21-3-21H55q-20 0-20-20V73q0-20 20-20Z" fill="white" stroke="{orange}" stroke-width="5" opacity="{min(1,p*2):.2f}"/>',
                 f'<path d="M287 40h178q20 0 20 20v48q0 20-20 20h-80l-23 22-1-22h-74q-20 0-20-20V60q0-20 20-20Z" fill="white" stroke="{teal}" stroke-width="5" opacity="{min(1,max(0,(p-.3)*2)):.2f}"/>',
                 f'<path d="M78 88h134m-134 22h85M309 74h132m-132 22h93" stroke="#8ba7ba" stroke-width="6" stroke-linecap="round"/>']
    elif name == "growth_steps":
        heights = (57, 108, 155)
        for i,h in enumerate(heights):
            shown = h * p
            x = 90 + i * 125
            base.append(f'<rect x="{x}" y="{236-shown:.1f}" width="75" height="{shown:.1f}" rx="9" fill="{(blue,teal,orange)[i]}"/>')
        base += [f'<path d="M67 251h415" stroke="{ink}" stroke-width="5"/>',
                 f'<path d="M83 183Q215 188 310 105T446 58" fill="none" stroke="{ink}" stroke-width="6" stroke-linecap="round" opacity="{p:.2f}"/>',
                 f'<path d="M422 55l27-2-5 27" fill="none" stroke="{ink}" stroke-width="6" stroke-linejoin="round" opacity="{p:.2f}"/>']
    elif name == "data_network":
        nodes = ((106,154),(183,72),(192,218),(286,143),(373,80),(415,218))
        links = ((0,1),(0,2),(1,3),(2,3),(3,4),(3,5),(4,5))
        for a,b in links:
            x1,y1=nodes[a];x2,y2=nodes[b]
            base.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{blue}" stroke-width="7" opacity="{p:.2f}"/>')
        for i,(x,y) in enumerate(nodes):
            color=(orange,teal,blue)[i%3]
            base.append(f'<circle cx="{x}" cy="{y}" r="{20 if i==3 else 15}" fill="white" stroke="{color}" stroke-width="6" opacity="{min(1,p*2):.2f}"/>')
        base.append(f'<circle cx="286" cy="143" r="8" fill="{orange}" opacity="{p:.2f}"/>')
    elif name == "balance_scale":
        base += [f'<path d="M260 78v163M202 247h116" stroke="{ink}" stroke-width="10" stroke-linecap="round"/>',
                 f'<circle cx="260" cy="82" r="15" fill="{orange}"/>',
                 f'<path d="M105 105h310" stroke="{blue}" stroke-width="8" stroke-linecap="round"/>',
                 f'<path d="M150 105v96m220-96v96" stroke="{ink}" stroke-width="5"/>',
                 f'<path d="M88 202q62 62 124 0Z" fill="#d9e9f1" stroke="{blue}" stroke-width="5"/>',
                 f'<path d="M308 202q62 62 124 0Z" fill="#d9e9f1" stroke="{teal}" stroke-width="5"/>',
                 f'<circle cx="151" cy="184" r="19" fill="{orange}" opacity="{p:.2f}"/>',
                 f'<rect x="344" y="153" width="53" height="37" rx="7" fill="{teal}" opacity="{p:.2f}"/>']
    elif name == "wallet_payment":
        base += [f'<rect x="67" y="107" width="272" height="150" rx="24" fill="#dcae72" stroke="{ink}" stroke-width="6"/>',
                 f'<path d="M68 130q-18-74 74-78h166v57" fill="#f0c590" stroke="{ink}" stroke-width="6"/>',
                 f'<rect x="221" y="152" width="137" height="64" rx="16" fill="{teal}" stroke="{ink}" stroke-width="5"/>',
                 '<circle cx="258" cy="184" r="11" fill="white"/>',
                 f'<rect x="342" y="66" width="119" height="78" rx="12" fill="white" stroke="{blue}" stroke-width="5" opacity="{p:.2f}"/>',
                 f'<path d="M356 93h92m-92 21h48" stroke="{orange}" stroke-width="8" stroke-linecap="round" opacity="{p:.2f}"/>',
                 f'<circle cx="408" cy="216" r="35" fill="#f5ca59" stroke="{orange}" stroke-width="6" opacity="{p:.2f}"/>']
    elif name == "search_document":
        base += [f'<path d="M110 38h215l63 64v163H110Z" fill="white" stroke="{blue}" stroke-width="6"/>',
                 f'<path d="M325 38v64h63" fill="none" stroke="{blue}" stroke-width="6"/>',
                 '<path d="M146 105h124m-124 29h174m-174 29h155m-155 29h120" stroke="#9db6c7" stroke-width="7" stroke-linecap="round"/>',
                 f'<circle cx="335" cy="181" r="52" fill="white" fill-opacity=".72" stroke="{teal}" stroke-width="8" opacity="{p:.2f}"/>',
                 f'<path d="M372 219l71 61" stroke="{ink}" stroke-width="14" stroke-linecap="round" opacity="{p:.2f}"/>',
                 f'<path d="M310 180h50" stroke="{orange}" stroke-width="8" stroke-linecap="round" opacity="{p:.2f}"/>']
    elif name == "secure_lock":
        base += [f'<path d="M177 43l126 37v73q0 85-126 128Q51 238 51 153V80Z" fill="white" stroke="{blue}" stroke-width="7"/>',
                 f'<path d="M177 72l91 26v55q0 62-91 94-91-32-91-94V98Z" fill="#dcefeb"/>',
                 f'<path d="M143 154v-24q0-34 34-34t34 34v24" fill="none" stroke="{teal}" stroke-width="10"/>',
                 f'<rect x="128" y="150" width="98" height="73" rx="12" fill="{teal}"/>',
                 '<circle cx="177" cy="177" r="9" fill="white"/><path d="M177 185v18" stroke="white" stroke-width="6"/>',
                 f'<circle cx="397" cy="140" r="58" fill="white" stroke="{orange}" stroke-width="6" opacity="{p:.2f}"/>',
                 f'<path d="M370 142l18 18 38-42" fill="none" stroke="{teal}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" opacity="{p:.2f}"/>']
    elif name == "storyboard":
        for i in range(3):
            x=46+i*158
            color=(blue,teal,orange)[i]
            base.append(f'<rect x="{x}" y="77" width="139" height="115" rx="13" fill="white" stroke="{color}" stroke-width="5"/>')
            base.append(f'<circle cx="{x+42}" cy="116" r="17" fill="#dce8ef"/>')
            base.append(f'<path d="M{x+18} 170l36-35 29 25 22-19 22 29" fill="none" stroke="{color}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
        base += [f'<path d="M64 230h391" stroke="{ink}" stroke-width="6" stroke-linecap="round"/>',
                 f'<circle cx="{64+391*p:.1f}" cy="230" r="13" fill="{orange}"/>',
                 f'<path d="M247 38l38 23-38 23Z" fill="{orange}" opacity="{p:.2f}"/>']
    base.append('</svg>')
    return ''.join(base)
