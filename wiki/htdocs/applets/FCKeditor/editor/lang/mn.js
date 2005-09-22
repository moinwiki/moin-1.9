/*
 * FCKeditor - The text editor for internet
 * Copyright (C) 2003-2005 Frederico Caldeira Knabben
 * 
 * Licensed under the terms of the GNU Lesser General Public License:
 * 		http://www.opensource.org/licenses/lgpl-license.php
 * 
 * For further information visit:
 * 		http://www.fckeditor.net/
 * 
 * "Support Open Source software. What about a donation today?"
 * 
 * File Name: mn.js
 * 	Mongolian language file.
 * 
 * File Authors:
 * 		Lkamtseren ODONBAATAR (odonbaatarl@yahoo.com)
 */

var FCKLang =
{
// Хэлний чиглэл : "ltr" (left to right зүүнээс баруун ) буюу "rtl" (right to left баруунаас зүүн ).
Dir					: "ltr",

ToolbarCollapse		: "Багажны хэсэг эвдэх",
ToolbarExpand		: "Багажны хэсэг өргөтгөх",

// Менюний агуулга ба Toolbar-ийн элэментүүд
Save				: "Хадгалах",
NewPage				: "Шинэ хуудас",
Preview				: "Уридчлан харах",
Cut					: "Хайчлах",
Copy				: "Хуулах",
Paste				: "Буулгах",
PasteText			: "plain text-ээс буулгах",
PasteWord			: "Word-оос буулгах",
Print				: "Хэвлэх",
SelectAll			: "Бүгдийг нь сонгох",
RemoveFormat		: "Формат авч хаях",
InsertLinkLbl		: "Линк",
InsertLink			: "Линк Оруулах/Засварлах",
RemoveLink			: "Линк авч хаях",
InsertImageLbl		: "Зураг",
InsertImage			: "Зураг Оруулах/Засварлах",
InsertTableLbl		: "Хүснэгт",
InsertTable			: "Хүснэгт Оруулах/Засварлах",
InsertLineLbl		: "Зураас",
InsertLine			: "Хөндлөн зураас оруулах",
InsertSpecialCharLbl: "Онцгой тэмдэгт",
InsertSpecialChar	: "Онцгой тэмдэгт оруулах",
InsertSmileyLbl		: "Тодорхойлолт",
InsertSmiley		: "Тодорхойлолт оруулах",
About				: "FCKeditor-н тухай",
Bold				: "Тод бүдүүн",
Italic				: "Налуу",
Underline			: "Доогуур нь зураастай болгох",
StrikeThrough		: "Дундуур нь зураастай болгох",
Subscript			: "Суурь болгох",
Superscript			: "Зэрэг болгох",
LeftJustify			: "Зүүн талд байрлуулах",
CenterJustify		: "Төвд байрлуулах",
RightJustify		: "Баруун талд байрлуулах",
BlockJustify		: "Блок хэлбэрээр байрлуулах",
DecreaseIndent		: "Догол мөр нэмэх",
IncreaseIndent		: "Догол мөр хасах",
Undo				: "Хүчингүй болгох",
Redo				: "Өмнөх үйлдлээ сэргээх",
NumberedListLbl		: "Дугаарлагдсан жагсаалт",
NumberedList		: "Дугаарлагдсан жагсаалт Оруулах/Авах",
BulletedListLbl		: "Цэгтэй жагсаалт",
BulletedList		: "Цэгтэй жагсаалт Оруулах/Авах",
ShowTableBorders	: "Хүснэгтийн хүрээг үзүүлэх",
ShowDetails			: "Деталчлан үзүүлэх",
Style				: "Загвар",
FontFormat			: "Формат",
Font				: "Фонт",
FontSize			: "Хэмжээ",
TextColor			: "Фонтны өнгө",
BGColor				: "Фонны өнгө",
Source				: "Код",
Find				: "Хайх",
Replace				: "Солих",

// Менюний агуулга
EditLink			: "Холбоос засварлах",
InsertRow			: "Мөр оруулах",
DeleteRows			: "Мөр устгах",
InsertColumn		: "Багана оруулах",
DeleteColumns		: "Багана устгах",
InsertCell			: "Нүх оруулах",
DeleteCells			: "Нүх устгах",
MergeCells			: "Нүх нэгтэх",
SplitCell			: "Нүх тусгайрлах",
CellProperties		: "Хоосон зайн шинж чанар",
TableProperties		: "Хүснэгт",
ImageProperties		: "Зураг",

FontFormats			: "Хэвийн;Formatted;Хаяг;Heading 1;Heading 2;Heading 3;Heading 4;Heading 5;Heading 6;Paragraph (DIV)",	// 2.0: The last entry has been added.

// Дохио ба Message-үүд
ProcessingXHTML		: "XHTML үйл явц явагдаж байна. Хүлээнэ үү...",
Done				: "Хийх",
PasteWordConfirm	: "Word-оос хуулсан текстээ санаж байгааг нь буулгахыг та хүсч байна уу. Та текст-ээ буулгахын өмнө цэвэрлэх үү?",
NotCompatiblePaste	: "Энэ комманд Internet Explorer-ын 5.5 буюу түүнээс дээш хувилбарт идвэхшинэ. Та цэвэрлэхгүйгээр буулгахыг хүсч байна?",
UnknownToolbarItem	: "Багажны хэсгийн \"%1\" item мэдэгдэхгүй байна",
UnknownCommand		: "\"%1\" комманд нэр мэдагдэхгүй байна",
NotImplemented		: "Зөвшөөрөгдөхгүй комманд",
UnknownToolbarSet	: "Багажны хэсэгт \"%1\" оноох, үүсээгүй байна",

// Харилцах цонх буюу Dialogs
DlgBtnOK			: "OK",
DlgBtnCancel		: "Болих",
DlgBtnClose			: "Хаах",
DlgAdvancedTag		: "Нэмэлт",

// General Dialogs Labels
DlgGenNotSet		: "&lt;Оноохгүй&gt;",
DlgGenId			: "Id",
DlgGenLangDir		: "Хэлний чиглэл",
DlgGenLangDirLtr	: "Зүүнээс баруун (LTR)",
DlgGenLangDirRtl	: "Баруунаас зүүн (RTL)",
DlgGenLangCode		: "Хэлний код",
DlgGenAccessKey		: "Холбох түлхүүр",
DlgGenName			: "Нэр",
DlgGenTabIndex		: "Tab индекс",
DlgGenLongDescr		: "URL-ын тайлбар",
DlgGenClass			: "Stylesheet классууд",
DlgGenTitle			: "Зөвлөлдөх гарчиг",
DlgGenContType		: "Зөвлөлдөх төрлийн агуулга",
DlgGenLinkCharset	: "Тэмдэгт оноох нөөцөд холбогдсон",
DlgGenStyle			: "Загвар",

// Image Dialog буюу Харилцах Зураг
DlgImgTitle			: "Зураг",
DlgImgInfoTab		: "Зурагны мэдээлэл",
DlgImgBtnUpload		: "Үүнийг сервэррүү илгээ",
DlgImgURL			: "URL",
DlgImgUpload		: "Хуулах",
DlgImgBtnBrowse		: "Үйлчилгээ үзүүлэх",
DlgImgAlt			: "Тайлбар текст",
DlgImgWidth			: "Өргөн",
DlgImgHeight		: "Өндөр",
DlgImgLockRatio		: "Lock Ratio",
DlgBtnResetSize		: "хэмжээ дахин оноох",
DlgImgBorder		: "Хүрээ",
DlgImgHSpace		: "Хөндлөн зай",
DlgImgVSpace		: "Босоо зай",
DlgImgAlign			: "Эгнээ",
DlgImgAlignLeft		: "Зүүн",
DlgImgAlignAbsBottom: "Abs доод талд",
DlgImgAlignAbsMiddle: "Abs Дунд талд",
DlgImgAlignBaseline	: "Baseline",
DlgImgAlignBottom	: "Доод талд",
DlgImgAlignMiddle	: "Дунд талд",
DlgImgAlignRight	: "Баруун",
DlgImgAlignTextTop	: "Текст дээр",
DlgImgAlignTop		: "Дээд талд",
DlgImgPreview		: "Уридчлан харах",
DlgImgMsgWrongExt	: "Уучлаарай, Зөвхөн дараагийн файл төрлүүдийг хуулхыг зөвшөөрнө:\n\n" + FCKConfig.ImageUploadAllowedExtensions + "\n\n Үйлдэл зогссон.",
DlgImgAlertSelect	: "Зонгосон зургаа хуулна уу.",
DlgImgAlertUrl		: "Зурагны URL-ын төрлийн сонгоно уу",

// Link Dialog
DlgLnkWindowTitle	: "Линк",
DlgLnkInfoTab		: "Линкийн мэдээлэл",
DlgLnkTargetTab		: "Байрлал",

DlgLnkType			: "Линкийн төрөл",
DlgLnkTypeURL		: "URL",
DlgLnkTypeAnchor	: "Энэ хуудасандах холбоос",
DlgLnkTypeEMail		: "E-Mail",
DlgLnkProto			: "Протокол",
DlgLnkProtoOther	: "&lt;бусад&gt;",
DlgLnkURL			: "URL",
DlgLnkBtnBrowse		: "Үйлчилгэ үзүүлэх",
DlgLnkAnchorSel		: "Холбоос сонгох",
DlgLnkAnchorByName	: "Холбоосын нэрээр",
DlgLnkAnchorById	: "Элемэнт Id-гаар",
DlgLnkNoAnchors		: "&lt;Баримт бичиг холбоосгүй байна&gt;",
DlgLnkEMail			: "E-Mail Хаяг",
DlgLnkEMailSubject	: "Message Subject",
DlgLnkEMailBody		: "Message-ийн агуулга",
DlgLnkUpload		: "Хуулах",
DlgLnkBtnUpload		: "Үүнийг серверрүү илгээ",

DlgLnkTarget		: "Байрлал",
DlgLnkTargetFrame	: "&lt;Агуулах хүрээ&gt;",
DlgLnkTargetPopup	: "&lt;popup цонх&gt;",
DlgLnkTargetBlank	: "Шинэ цонх (_blank)",
DlgLnkTargetParent	: "Эцэг цонх (_parent)",
DlgLnkTargetSelf	: "Төстэй цонх (_self)",
DlgLnkTargetTop		: "Хамгийн түрүүн байх цонх (_top)",
DlgLnkTargetFrame	: "Байрлалын хүрээний нэр",
DlgLnkPopWinName	: "Popup цонхны нэр",
DlgLnkPopWinFeat	: "Popup цонхны онцлог",
DlgLnkPopResize		: "Хэмжээ өөрчлөх",
DlgLnkPopLocation	: "Location хэсэг",
DlgLnkPopMenu		: "Meню хэсэг",
DlgLnkPopScroll		: "Скрол хэсэгүүд",
DlgLnkPopStatus		: "Статус хэсэг",
DlgLnkPopToolbar	: "Багажны хэсэг",
DlgLnkPopFullScrn	: "Цонх дүүргэх (IE)",
DlgLnkPopDependent	: "Хамаатай (Netscape)",
DlgLnkPopWidth		: "Өргөн",
DlgLnkPopHeight		: "Өндөр",
DlgLnkPopLeft		: "Зүүн байрлал",
DlgLnkPopTop		: "Дээд байрлал",

DlgLnkMsgWrongExtA	: "Уучлайрай, Зөвхөн дараах файлын төрлүүдийг хуулахыг зөвшөөрнө:\n\n" + FCKConfig.LinkUploadAllowedExtensions + "\n\n Үйлдэл зогссон.",
DlgLnkMsgWrongExtD	: "Уучлайрай, Зөвхөн дараах файлын төрлүүдийг хуулахыг зөвшөөрөхгүй:\n\n" + FCKConfig.LinkUploadDeniedExtensions + "\n\n Үйлдэл зогссон.",

DlnLnkMsgNoUrl		: "Линк URL-ээ төрөлжүүлнэ үү",
DlnLnkMsgNoEMail	: "Е-mail хаягаа төрөлжүүлнэ үү",
DlnLnkMsgNoAnchor	: "Холбоосоо сонгоно уу",

// Color Dialog
DlgColorTitle		: "Өнгө сонгох",
DlgColorBtnClear	: "Цэвэрлэх",
DlgColorHighlight	: "Өнгө",
DlgColorSelected	: "Сонгогдсон",

// Smiley Dialog
DlgSmileyTitle		: "Тодорхойлолт оруулах",

// Special Character Dialog
DlgSpecialCharTitle	: "Онцгой тэмдэгт сонгох",

// Table Dialog
DlgTableTitle		: "Хүснэгт",
DlgTableRows		: "Мөр",
DlgTableColumns		: "Багана",
DlgTableBorder		: "Хүрээний хэмжээ",
DlgTableAlign		: "Эгнээ",
DlgTableAlignNotSet	: "&lt;Оноохгүй&gt;",
DlgTableAlignLeft	: "Зүүн талд",
DlgTableAlignCenter	: "Төвд",
DlgTableAlignRight	: "Баруун талд",
DlgTableWidth		: "Өргөн",
DlgTableWidthPx		: "цэг",
DlgTableWidthPc		: "хувь",
DlgTableHeight		: "Өндөр",
DlgTableCellSpace	: "Нүх хоорондын зай",
DlgTableCellPad		: "Нүх доторлох",
DlgTableCaption		: "Тайлбар",

// Table Cell Dialog
DlgCellTitle		: "Хоосон зайн шинж чанар",
DlgCellWidth		: "Өргөн",
DlgCellWidthPx		: "цэг",
DlgCellWidthPc		: "хувь",
DlgCellHeight		: "Өндөр",
DlgCellWordWrap		: "Үг таслах",
DlgCellWordWrapNotSet	: "&lt;Оноохгүй&gt;",
DlgCellWordWrapYes	: "Тийм",
DlgCellWordWrapNo	: "Үгүй",
DlgCellHorAlign		: "Босоо эгнээ",
DlgCellHorAlignNotSet	: "&lt;Оноохгүй&gt;",
DlgCellHorAlignLeft	: "Зүүн",
DlgCellHorAlignCenter	: "Төв",
DlgCellHorAlignRight: "Баруун",
DlgCellVerAlign		: "Хөндлөн эгнээ",
DlgCellVerAlignNotSet	: "&lt;Оноохгүй&gt;",
DlgCellVerAlignTop	: "Дээд тал",
DlgCellVerAlignMiddle	: "Дунд",
DlgCellVerAlignBottom	: "Доод тал",
DlgCellVerAlignBaseline	: "Baseline",
DlgCellRowSpan		: "Нийт мөр",
DlgCellCollSpan		: "Нийт багана",
DlgCellBackColor	: "Фонны өнгө",
DlgCellBorderColor	: "Хүрээний өнгө",
DlgCellBtnSelect	: "Сонго...",

// Find Dialog
DlgFindTitle		: "Хайх",
DlgFindFindBtn		: "Хайх",
DlgFindNotFoundMsg	: "Хайсан текст олсонгүй.",

// Replace Dialog
DlgReplaceTitle			: "Солих",
DlgReplaceFindLbl		: "Хайх үг/үсэг:",
DlgReplaceReplaceLbl	: "Солих үг:",
DlgReplaceCaseChk		: "Тэнцэх төлөв",
DlgReplaceReplaceBtn	: "Солих",
DlgReplaceReplAllBtn	: "Бүгдийг нь Солих",
DlgReplaceWordChk		: "Тэнцэх бүтэн үг",

// Paste Operations / Dialog
PasteErrorPaste	: "Таны browser-ын хамгаалалтын тохиргоо editor-д автоматаар буулгах үйлдэлийг зөвшөөрөхгүй байна. (Ctrl+V) товчны хослолыг ашиглана уу.",
PasteErrorCut	: "Таны browser-ын хамгаалалтын тохиргоо editor-д автоматаар хайчлах үйлдэлийг зөвшөөрөхгүй байна. (Ctrl+X) товчны хослолыг ашиглана уу.",
PasteErrorCopy	: "Таны browser-ын хамгаалалтын тохиргоо editor-д автоматаар хуулах үйлдэлийг зөвшөөрөхгүй байна. (Ctrl+C) товчны хослолыг ашиглана уу.",

PasteAsText		: "Plain Text-ээс буулгах",
PasteFromWord	: "Word-оос буулгах",

DlgPasteMsg		: "Editor автоматаар буулгах үйлдэлийг хийх чадахгүй байсан. яагаад гэвэл таны browser-ын <STRONG>хамгаалалтын тохиргоо</STRONG> зөвшөөрөхгүй байна.<BR> Хаалтандах товчны хослолыг ашиглан буулгана уу (<STRONG>Ctrl+V</STRONG>), <STRONG>OK</STRONG>.",

// Color Picker
ColorAutomatic	: "Автоматаар",
ColorMoreColors	: "Нэмэлт өнгөнүүд...",

// About Dialog
DlgAboutVersion	: "Хувилбар",
DlgAboutLicense	: "GNU цөөн ерөнхий нийтийн лицензийн ангилалд багтсан зөвшөөрөлтэй",
DlgAboutInfo	: "Мэдээллээр туслах"
}