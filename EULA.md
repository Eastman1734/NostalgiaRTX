# Лицензионное соглашение с конечным пользователем (EULA) — Nostalgia RTX

# End User License Agreement (EULA) — Nostalgia RTX

Версия 1.0 / Version 1.0. Применяется к Nostalgia RTX 0.2.2 и более поздним версиям / Applies to Nostalgia RTX 0.2.2 and later.

---

## RU — Русская версия

Это соглашение между вами («Пользователь») и Александром Балиным («Лицензиар») об использовании программы Nostalgia RTX («Программа»). Устанавливая или запуская Программу, вы принимаете это соглашение. Если вы не согласны, не устанавливайте и не используйте Программу и удалите все её копии.

### 1. Состав Программы

Программа состоит из (а) оригинального кода Лицензиара и (б) сторонних компонентов, включая проприетарные компоненты NVIDIA RTX Video SDK 1.1 («Компоненты NVIDIA»): библиотеку `nvngx_vsr.dll` и объектный код NVIDIA, связанный с `nostalgia_rtx.dll`. Программа содержит исходный код, предоставленный NVIDIA Corporation («NVIDIA»). Компоненты NVIDIA являются частью Программы и не лицензируются как самостоятельный продукт.

### 2. Лицензия

Лицензиар предоставляет вам неисключительную, непередаваемую лицензию без права сублицензирования на установку и использование Программы на принадлежащих вам или находящихся под вашим контролем компьютерах с видеокартами NVIDIA, для обработки видео. Компоненты NVIDIA лицензируются только для использования в составе Программы. Оригинальный код Лицензиара вы можете изменять для собственного использования. Лицензии сторонних компонентов (Python, Qt for Python, NumPy, Pillow, FFmpeg и др.) не заменяются и не отменяются этим соглашением; они перечислены в `THIRD-PARTY-NOTICES.md`.

### 3. Ограничения

Вы не вправе:

1. декомпилировать, дизассемблировать или иным образом восстанавливать исходный код Компонентов NVIDIA, а также удалять или изменять уведомления об авторских правах и другие уведомления о правах собственности;
2. копировать, продавать, сдавать в аренду, передавать, распространять, сублицензировать или изменять Компоненты NVIDIA, кроме как в составе неизменённой Программы; в частности, распространять `nvngx_vsr.dll` или `nostalgia_rtx.dll` как самостоятельный продукт или отдельно от Программы;
3. обходить, отключать или нарушать любые технические ограничения, шифрование, защитные механизмы или механизмы аутентификации в Компонентах NVIDIA;
4. использовать Компоненты NVIDIA так, чтобы они подпали под условия лицензии на открытое программное обеспечение, требующей раскрытия исходного кода, права на создание производных работ или бесплатного распространения;
5. использовать Программу в системах, отказ или сбой которых может привести к травме, смерти или катастрофическому ущербу, включая авионику, навигацию, военные, медицинские и жизнеобеспечивающие системы;
6. указывать или создавать впечатление, что Программа одобрена, спонсируется или поддерживается NVIDIA;
7. использовать товарные знаки NVIDIA, кроме как для указания на совместимость и атрибуции в документации Программы.

### 4. Права NVIDIA и третьих лиц

NVIDIA и её поставщики сохраняют все права на Компоненты NVIDIA, включая права на интеллектуальную собственность. NVIDIA и RTX являются товарными знаками или зарегистрированными товарными знаками NVIDIA Corporation. Программа является самостоятельным приложением и не является продуктом NVIDIA.

NVIDIA может предоставлять обновления Компонентов NVIDIA. Содержание и форма Компонентов NVIDIA могут изменяться без предварительного уведомления. NVIDIA является третьей стороной — бенефициаром ограничений и отказов от гарантий и ответственности, относящихся к Компонентам NVIDIA в этом соглашении.

### 5. Конфиденциальность и безопасность

Программа обрабатывает видео локально на вашем компьютере и не передаёт ваши видео, изображения или результаты обработки Лицензиару или третьим лицам. Сетевое соединение используется только установщиком для загрузки закреплённых по версии и контрольной сумме компонентов (Python, Qt, NumPy, Pillow, FFmpeg) с указанных в `scripts/dependencies.json` адресов. Журналы и сравнительные кадры сохраняются только на вашем компьютере в `%LOCALAPPDATA%\NostalgiaRTX\sessions`.

### 6. Права на обрабатываемые материалы

Вы отвечаете за то, что имеете право обрабатывать видео, которые вы загружаете в Программу, и за соблюдение применимого законодательства и прав третьих лиц. Лицензиар не получает прав на ваши видео и результаты.

### 7. Кодеки

Программа использует FFmpeg и аппаратный кодировщик NVENC для кодирования видео. Вы самостоятельно отвечаете за получение любых лицензий на аудио- и видеокодеки и связанные патенты, которые могут требоваться для вашего использования результатов (в том числе в коммерческих целях). Ни Лицензиар, ни NVIDIA не предоставляют таких прав.

### 8. Экспортный контроль

Компоненты NVIDIA подпадают под экспортное законодательство США, включая Export Administration Regulations (EAR) и санкции OFAC. Вы обязуетесь соблюдать применимое экспортное законодательство и подтверждаете, что не проживаете в стране или регионе, находящемся под эмбарго США, и что вам не запрещено получать Программу.

### 9. Отказ от гарантий

ПРОГРАММА, В ТОМ ЧИСЛЕ КОМПОНЕНТЫ NVIDIA, ПРЕДОСТАВЛЯЕТСЯ «КАК ЕСТЬ». В МАКСИМАЛЬНО ДОПУСТИМОЙ ПРИМЕНИМЫМ ПРАВОМ СТЕПЕНИ ЛИЦЕНЗИАР И NVIDIA ОТКАЗЫВАЮТСЯ ОТ ЛЮБЫХ ЯВНЫХ, ПОДРАЗУМЕВАЕМЫХ И УСТАНОВЛЕННЫХ ЗАКОНОМ ГАРАНТИЙ, ВКЛЮЧАЯ ГАРАНТИИ ТОВАРНОГО КАЧЕСТВА, ПРИГОДНОСТИ ДЛЯ КОНКРЕТНОЙ ЦЕЛИ И НЕНАРУШЕНИЯ ПРАВ. НЕ ГАРАНТИРУЕТСЯ, ЧТО ПРОГРАММА УДОВЛЕТВОРИТ ВАШИ ТРЕБОВАНИЯ, БУДЕТ РАБОТАТЬ БЕЗ ПЕРЕБОЕВ ИЛИ БЕЗ ОШИБОК. Эта версия Программы экспериментальная; её работа на конкретных устройствах и драйверах не гарантируется.

### 10. Ограничение ответственности

В МАКСИМАЛЬНО ДОПУСТИМОЙ ПРИМЕНИМЫМ ПРАВОМ СТЕПЕНИ ЛИЦЕНЗИАР И NVIDIA НЕ НЕСУТ ОТВЕТСТВЕННОСТИ ЗА КОСВЕННЫЕ, ОСОБЫЕ, СЛУЧАЙНЫЕ, ШТРАФНЫЕ ИЛИ ПОСЛЕДУЮЩИЕ УБЫТКИ, УПУЩЕННУЮ ВЫГОДУ, ПОТЕРЮ ДАННЫХ ИЛИ ВРЕМЕНИ, ВОЗНИКШИЕ В СВЯЗИ С ПРОГРАММОЙ. ОБЩАЯ ОТВЕТСТВЕННОСТЬ NVIDIA ПО ЭТОМУ СОГЛАШЕНИЮ НЕ ПРЕВЫШАЕТ 10 ДОЛЛАРОВ США. Ничто в этом соглашении не исключает ответственность, которую нельзя исключить по закону.

### 11. Возмещение

Вы возмещаете Лицензиару и NVIDIA убытки и расходы, возникшие из-за использования вами Программы с нарушением этого соглашения.

### 12. Прекращение

Соглашение прекращается автоматически при нарушении любого его условия. После прекращения вы обязаны прекратить использование Программы и удалить все её копии. Разделы 3, 4, 8–11 и 13 сохраняют силу после прекращения.

### 13. Прочее

Если какое-либо положение признано недействительным, остальные сохраняют силу. Это соглашение — полное соглашение сторон по его предмету. Если не требуется иное по обязательным нормам права, соглашение толкуется по праву страны, в которой Лицензиар имеет постоянное место жительства. Для обращений к Лицензиару и сообщений о нарушениях используйте раздел Issues страницы Программы на GitHub.

---

## EN — English version

This agreement is between you ("User") and Aleksandr Balin ("Licensor") regarding the Nostalgia RTX software ("Software"). By installing or running the Software you accept this agreement. If you do not agree, do not install or use the Software and delete all copies.

### 1. Contents

The Software consists of (a) the Licensor's original code and (b) third-party components, including proprietary components of NVIDIA RTX Video SDK 1.1 ("NVIDIA Components"): the `nvngx_vsr.dll` library and NVIDIA object code linked into `nostalgia_rtx.dll`. This software contains source code provided by NVIDIA Corporation ("NVIDIA"). The NVIDIA Components are part of the Software and are not licensed as a stand-alone product.

### 2. License

The Licensor grants you a non-exclusive, non-transferable license, without the right to sublicense, to install and use the Software on computers you own or control that have NVIDIA GPUs, to process video. The NVIDIA Components are licensed only for use as part of the Software. You may modify the Licensor's original code for your own use. Licenses of third-party components (Python, Qt for Python, NumPy, Pillow, FFmpeg, etc.) are neither replaced nor overridden by this agreement; they are listed in `THIRD-PARTY-NOTICES.md`.

### 3. Restrictions

You may not:

1. reverse engineer, decompile or disassemble the NVIDIA Components, or remove copyright or other proprietary notices;
2. copy, sell, rent, sublicense, transfer, distribute or modify the NVIDIA Components, except as part of the unmodified Software; in particular, you may not distribute `nvngx_vsr.dll` or `nostalgia_rtx.dll` as a stand-alone product or separately from the Software;
3. bypass, disable or circumvent any technical limitation, encryption, security, DRM or authentication mechanism in the NVIDIA Components;
4. use the NVIDIA Components in any manner that would cause them to become subject to an open source license requiring disclosure of source code, licensing for derivative works, or redistribution at no charge;
5. use the Software in any system where its use or failure can reasonably be expected to threaten or result in personal injury, death or catastrophic loss, including avionics, navigation, military, medical and life-support systems;
6. indicate or imply that the Software is sponsored or endorsed by NVIDIA;
7. use NVIDIA trademarks except to state compatibility and for attribution in the Software's documentation.

### 4. Rights of NVIDIA and third parties

NVIDIA and its suppliers retain all rights in the NVIDIA Components, including intellectual property rights. NVIDIA and RTX are trademarks or registered trademarks of NVIDIA Corporation. The Software is an independent application and is not an NVIDIA product.

NVIDIA may make updates to the NVIDIA Components available. The form and content of the NVIDIA Components may change without prior notice. NVIDIA is an intended third-party beneficiary of the restrictions and the disclaimers of warranty and liability in this agreement that relate to the NVIDIA Components.

### 5. Privacy and security

The Software processes video locally on your computer and does not transmit your videos, images or processing results to the Licensor or any third party. The network is used only by the installer to download version- and checksum-pinned components (Python, Qt, NumPy, Pillow, FFmpeg) from the addresses listed in `scripts/dependencies.json`. Logs and comparison frames are stored only on your computer in `%LOCALAPPDATA%\NostalgiaRTX\sessions`.

### 6. Your content

You are responsible for having the right to process the videos you load into the Software and for complying with applicable law and third-party rights. The Licensor acquires no rights in your videos or outputs.

### 7. Codecs

The Software uses FFmpeg and the NVENC hardware encoder to encode video. You are solely responsible for obtaining any licenses for audio and video codecs and related patents that may be required for your use of the output (including commercial use). Neither the Licensor nor NVIDIA grants such rights.

### 8. Export control

The NVIDIA Components are subject to United States export laws, including the Export Administration Regulations (EAR) and OFAC sanctions. You agree to comply with applicable export laws and confirm that you do not reside in a country or region embargoed by the United States and are not otherwise prohibited from receiving the Software.

### 9. Disclaimer of warranties

THE SOFTWARE, INCLUDING THE NVIDIA COMPONENTS, IS PROVIDED "AS IS". TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE LICENSOR AND NVIDIA DISCLAIM ALL WARRANTIES OF ANY KIND, WHETHER EXPRESS, IMPLIED OR STATUTORY, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. THERE IS NO WARRANTY THAT THE SOFTWARE WILL MEET YOUR REQUIREMENTS OR OPERATE UNINTERRUPTED OR ERROR-FREE. This version is experimental; operation on particular hardware and drivers is not guaranteed.

### 10. Limitation of liability

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE LICENSOR AND NVIDIA SHALL NOT BE LIABLE FOR ANY INDIRECT, SPECIAL, INCIDENTAL, PUNITIVE OR CONSEQUENTIAL DAMAGES, LOST PROFITS, OR LOSS OF DATA OR TIME ARISING OUT OF THE SOFTWARE. NVIDIA'S TOTAL CUMULATIVE LIABILITY UNDER THIS AGREEMENT SHALL NOT EXCEED US$10.00. Nothing in this agreement excludes liability that cannot be excluded by law.

### 11. Indemnification

You will indemnify the Licensor and NVIDIA against losses and expenses arising from your use of the Software in breach of this agreement.

### 12. Termination

This agreement terminates automatically if you breach any of its terms. Upon termination you must stop using the Software and delete all copies. Sections 3, 4, 8–11 and 13 survive termination.

### 13. General

If any provision is held invalid, the remainder stays in force. This is the entire agreement of the parties on its subject. Unless mandatory law requires otherwise, this agreement is governed by the law of the country where the Licensor has permanent residence. To contact the Licensor or report violations, use the Issues section of the Software's GitHub page.
