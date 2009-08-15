"""
    MoinMoin - convert from html to wiki markup

    @copyright: 2005-2006 Bastian Blank, Florian Festi, Reimar Bauer,
                2005-2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import re, os
import xml.dom.minidom # HINT: the nodes in parse result tree need .has_key(), "x in ..." does not work
from xml.dom import Node

from MoinMoin import config, wikiutil
from MoinMoin.error import ConvertError

from MoinMoin.parser.text_moin_wiki import Parser as WikiParser
interwiki_re = re.compile(WikiParser.interwiki_rule, re.VERBOSE|re.UNICODE)

# Portions (C) International Organization for Standardization 1986
# Permission to copy in any form is granted for use with
# conforming SGML systems and applications as defined in
# ISO 8879, provided this notice is included in all copies.
dtd = ur'''
<!DOCTYPE html [
<!ENTITY nbsp   "&#32;">  <!-- no-break space = non-breaking space, U+00A0, convert to U+0020 -->
<!ENTITY iexcl  "&#161;"> <!-- inverted exclamation mark, U+00A1 ISOnum -->
<!ENTITY cent   "&#162;"> <!-- cent sign, U+00A2 ISOnum -->
<!ENTITY pound  "&#163;"> <!-- pound sign, U+00A3 ISOnum -->
<!ENTITY curren "&#164;"> <!-- currency sign, U+00A4 ISOnum -->
<!ENTITY yen    "&#165;"> <!-- yen sign = yuan sign, U+00A5 ISOnum -->
<!ENTITY brvbar "&#166;"> <!-- broken bar = broken vertical bar, U+00A6 ISOnum -->
<!ENTITY sect   "&#167;"> <!-- section sign, U+00A7 ISOnum -->
<!ENTITY uml    "&#168;"> <!-- diaeresis = spacing diaeresis, U+00A8 ISOdia -->
<!ENTITY copy   "&#169;"> <!-- copyright sign, U+00A9 ISOnum -->
<!ENTITY ordf   "&#170;"> <!-- feminine ordinal indicator, U+00AA ISOnum -->
<!ENTITY laquo  "&#171;"> <!-- left-pointing double angle quotation mark = left pointing guillemet, U+00AB ISOnum -->
<!ENTITY not    "&#172;"> <!-- not sign = angled dash, U+00AC ISOnum -->
<!ENTITY shy    "&#173;"> <!-- soft hyphen = discretionary hyphen, U+00AD ISOnum -->
<!ENTITY reg    "&#174;"> <!-- registered sign = registered trade mark sign, U+00AE ISOnum -->
<!ENTITY macr   "&#175;"> <!-- macron = spacing macron = overline = APL overbar, U+00AF ISOdia -->
<!ENTITY deg    "&#176;"> <!-- degree sign, U+00B0 ISOnum -->
<!ENTITY plusmn "&#177;"> <!-- plus-minus sign = plus-or-minus sign, U+00B1 ISOnum -->
<!ENTITY sup2   "&#178;"> <!-- superscript two = superscript digit two = squared, U+00B2 ISOnum -->
<!ENTITY sup3   "&#179;"> <!-- superscript three = superscript digit three = cubed, U+00B3 ISOnum -->
<!ENTITY acute  "&#180;"> <!-- acute accent = spacing acute, U+00B4 ISOdia -->
<!ENTITY micro  "&#181;"> <!-- micro sign, U+00B5 ISOnum -->
<!ENTITY para   "&#182;"> <!-- pilcrow sign = paragraph sign, U+00B6 ISOnum -->
<!ENTITY middot "&#183;"> <!-- middle dot = Georgian comma = Greek middle dot, U+00B7 ISOnum -->
<!ENTITY cedil  "&#184;"> <!-- cedilla = spacing cedilla, U+00B8 ISOdia -->
<!ENTITY sup1   "&#185;"> <!-- superscript one = superscript digit one, U+00B9 ISOnum -->
<!ENTITY ordm   "&#186;"> <!-- masculine ordinal indicator, U+00BA ISOnum -->
<!ENTITY raquo  "&#187;"> <!-- right-pointing double angle quotation mark = right pointing guillemet, U+00BB ISOnum -->
<!ENTITY frac14 "&#188;"> <!-- vulgar fraction one quarter = fraction one quarter, U+00BC ISOnum -->
<!ENTITY frac12 "&#189;"> <!-- vulgar fraction one half = fraction one half, U+00BD ISOnum -->
<!ENTITY frac34 "&#190;"> <!-- vulgar fraction three quarters = fraction three quarters, U+00BE ISOnum -->
<!ENTITY iquest "&#191;"> <!-- inverted question mark = turned question mark, U+00BF ISOnum -->
<!ENTITY Agrave "&#192;"> <!-- latin capital letter A with grave = latin capital letter A grave, U+00C0 ISOlat1 -->
<!ENTITY Aacute "&#193;"> <!-- latin capital letter A with acute, U+00C1 ISOlat1 -->
<!ENTITY Acirc  "&#194;"> <!-- latin capital letter A with circumflex, U+00C2 ISOlat1 -->
<!ENTITY Atilde "&#195;"> <!-- latin capital letter A with tilde, U+00C3 ISOlat1 -->
<!ENTITY Auml   "&#196;"> <!-- latin capital letter A with diaeresis, U+00C4 ISOlat1 -->
<!ENTITY Aring  "&#197;"> <!-- latin capital letter A with ring above = latin capital letter A ring, U+00C5 ISOlat1 -->
<!ENTITY AElig  "&#198;"> <!-- latin capital letter AE = latin capital ligature AE, U+00C6 ISOlat1 -->
<!ENTITY Ccedil "&#199;"> <!-- latin capital letter C with cedilla, U+00C7 ISOlat1 -->
<!ENTITY Egrave "&#200;"> <!-- latin capital letter E with grave, U+00C8 ISOlat1 -->
<!ENTITY Eacute "&#201;"> <!-- latin capital letter E with acute, U+00C9 ISOlat1 -->
<!ENTITY Ecirc  "&#202;"> <!-- latin capital letter E with circumflex, U+00CA ISOlat1 -->
<!ENTITY Euml   "&#203;"> <!-- latin capital letter E with diaeresis, U+00CB ISOlat1 -->
<!ENTITY Igrave "&#204;"> <!-- latin capital letter I with grave, U+00CC ISOlat1 -->
<!ENTITY Iacute "&#205;"> <!-- latin capital letter I with acute, U+00CD ISOlat1 -->
<!ENTITY Icirc  "&#206;"> <!-- latin capital letter I with circumflex, U+00CE ISOlat1 -->
<!ENTITY Iuml   "&#207;"> <!-- latin capital letter I with diaeresis, U+00CF ISOlat1 -->
<!ENTITY ETH    "&#208;"> <!-- latin capital letter ETH, U+00D0 ISOlat1 -->
<!ENTITY Ntilde "&#209;"> <!-- latin capital letter N with tilde, U+00D1 ISOlat1 -->
<!ENTITY Ograve "&#210;"> <!-- latin capital letter O with grave, U+00D2 ISOlat1 -->
<!ENTITY Oacute "&#211;"> <!-- latin capital letter O with acute, U+00D3 ISOlat1 -->
<!ENTITY Ocirc  "&#212;"> <!-- latin capital letter O with circumflex, U+00D4 ISOlat1 -->
<!ENTITY Otilde "&#213;"> <!-- latin capital letter O with tilde, U+00D5 ISOlat1 -->
<!ENTITY Ouml   "&#214;"> <!-- latin capital letter O with diaeresis, U+00D6 ISOlat1 -->
<!ENTITY times  "&#215;"> <!-- multiplication sign, U+00D7 ISOnum -->
<!ENTITY Oslash "&#216;"> <!-- latin capital letter O with stroke = latin capital letter O slash, U+00D8 ISOlat1 -->
<!ENTITY Ugrave "&#217;"> <!-- latin capital letter U with grave, U+00D9 ISOlat1 -->
<!ENTITY Uacute "&#218;"> <!-- latin capital letter U with acute, U+00DA ISOlat1 -->
<!ENTITY Ucirc  "&#219;"> <!-- latin capital letter U with circumflex, U+00DB ISOlat1 -->
<!ENTITY Uuml   "&#220;"> <!-- latin capital letter U with diaeresis, U+00DC ISOlat1 -->
<!ENTITY Yacute "&#221;"> <!-- latin capital letter Y with acute, U+00DD ISOlat1 -->
<!ENTITY THORN  "&#222;"> <!-- latin capital letter THORN, U+00DE ISOlat1 -->
<!ENTITY szlig  "&#223;"> <!-- latin small letter sharp s = ess-zed, U+00DF ISOlat1 -->
<!ENTITY agrave "&#224;"> <!-- latin small letter a with grave = latin small letter a grave, U+00E0 ISOlat1 -->
<!ENTITY aacute "&#225;"> <!-- latin small letter a with acute, U+00E1 ISOlat1 -->
<!ENTITY acirc  "&#226;"> <!-- latin small letter a with circumflex, U+00E2 ISOlat1 -->
<!ENTITY atilde "&#227;"> <!-- latin small letter a with tilde, U+00E3 ISOlat1 -->
<!ENTITY auml   "&#228;"> <!-- latin small letter a with diaeresis, U+00E4 ISOlat1 -->
<!ENTITY aring  "&#229;"> <!-- latin small letter a with ring above = latin small letter a ring, U+00E5 ISOlat1 -->
<!ENTITY aelig  "&#230;"> <!-- latin small letter ae = latin small ligature ae, U+00E6 ISOlat1 -->
<!ENTITY ccedil "&#231;"> <!-- latin small letter c with cedilla, U+00E7 ISOlat1 -->
<!ENTITY egrave "&#232;"> <!-- latin small letter e with grave, U+00E8 ISOlat1 -->
<!ENTITY eacute "&#233;"> <!-- latin small letter e with acute, U+00E9 ISOlat1 -->
<!ENTITY ecirc  "&#234;"> <!-- latin small letter e with circumflex, U+00EA ISOlat1 -->
<!ENTITY euml   "&#235;"> <!-- latin small letter e with diaeresis, U+00EB ISOlat1 -->
<!ENTITY igrave "&#236;"> <!-- latin small letter i with grave, U+00EC ISOlat1 -->
<!ENTITY iacute "&#237;"> <!-- latin small letter i with acute, U+00ED ISOlat1 -->
<!ENTITY icirc  "&#238;"> <!-- latin small letter i with circumflex, U+00EE ISOlat1 -->
<!ENTITY iuml   "&#239;"> <!-- latin small letter i with diaeresis, U+00EF ISOlat1 -->
<!ENTITY eth    "&#240;"> <!-- latin small letter eth, U+00F0 ISOlat1 -->
<!ENTITY ntilde "&#241;"> <!-- latin small letter n with tilde, U+00F1 ISOlat1 -->
<!ENTITY ograve "&#242;"> <!-- latin small letter o with grave, U+00F2 ISOlat1 -->
<!ENTITY oacute "&#243;"> <!-- latin small letter o with acute, U+00F3 ISOlat1 -->
<!ENTITY ocirc  "&#244;"> <!-- latin small letter o with circumflex, U+00F4 ISOlat1 -->
<!ENTITY otilde "&#245;"> <!-- latin small letter o with tilde, U+00F5 ISOlat1 -->
<!ENTITY ouml   "&#246;"> <!-- latin small letter o with diaeresis, U+00F6 ISOlat1 -->
<!ENTITY divide "&#247;"> <!-- division sign, U+00F7 ISOnum -->
<!ENTITY oslash "&#248;"> <!-- latin small letter o with stroke, = latin small letter o slash, U+00F8 ISOlat1 -->
<!ENTITY ugrave "&#249;"> <!-- latin small letter u with grave, U+00F9 ISOlat1 -->
<!ENTITY uacute "&#250;"> <!-- latin small letter u with acute, U+00FA ISOlat1 -->
<!ENTITY ucirc  "&#251;"> <!-- latin small letter u with circumflex, U+00FB ISOlat1 -->
<!ENTITY uuml   "&#252;"> <!-- latin small letter u with diaeresis, U+00FC ISOlat1 -->
<!ENTITY yacute "&#253;"> <!-- latin small letter y with acute, U+00FD ISOlat1 -->
<!ENTITY thorn  "&#254;"> <!-- latin small letter thorn, U+00FE ISOlat1 -->
<!ENTITY yuml   "&#255;"> <!-- latin small letter y with diaeresis, U+00FF ISOlat1 -->

<!-- Latin Extended-B -->
<!ENTITY fnof     "&#402;"> <!-- latin small f with hook = function                                    = florin, U+0192 ISOtech -->

<!-- Greek -->
<!ENTITY Alpha    "&#913;"> <!-- greek capital letter alpha, U+0391 -->
<!ENTITY Beta     "&#914;"> <!-- greek capital letter beta, U+0392 -->
<!ENTITY Gamma    "&#915;"> <!-- greek capital letter gamma,
                                    U+0393 ISOgrk3 -->
<!ENTITY Delta    "&#916;"> <!-- greek capital letter delta,
                                    U+0394 ISOgrk3 -->
<!ENTITY Epsilon  "&#917;"> <!-- greek capital letter epsilon, U+0395 -->
<!ENTITY Zeta     "&#918;"> <!-- greek capital letter zeta, U+0396 -->
<!ENTITY Eta      "&#919;"> <!-- greek capital letter eta, U+0397 -->
<!ENTITY Theta    "&#920;"> <!-- greek capital letter theta,
                                    U+0398 ISOgrk3 -->
<!ENTITY Iota     "&#921;"> <!-- greek capital letter iota, U+0399 -->
<!ENTITY Kappa    "&#922;"> <!-- greek capital letter kappa, U+039A -->
<!ENTITY Lambda   "&#923;"> <!-- greek capital letter lambda,
                                    U+039B ISOgrk3 -->
<!ENTITY Mu       "&#924;"> <!-- greek capital letter mu, U+039C -->
<!ENTITY Nu       "&#925;"> <!-- greek capital letter nu, U+039D -->
<!ENTITY Xi       "&#926;"> <!-- greek capital letter xi, U+039E ISOgrk3 -->
<!ENTITY Omicron  "&#927;"> <!-- greek capital letter omicron, U+039F -->
<!ENTITY Pi       "&#928;"> <!-- greek capital letter pi, U+03A0 ISOgrk3 -->
<!ENTITY Rho      "&#929;"> <!-- greek capital letter rho, U+03A1 -->
<!-- there is no Sigmaf, and no U+03A2 character either -->
<!ENTITY Sigma    "&#931;"> <!-- greek capital letter sigma,
                                    U+03A3 ISOgrk3 -->
<!ENTITY Tau      "&#932;"> <!-- greek capital letter tau, U+03A4 -->
<!ENTITY Upsilon  "&#933;"> <!-- greek capital letter upsilon,
                                    U+03A5 ISOgrk3 -->
<!ENTITY Phi      "&#934;"> <!-- greek capital letter phi,
                                    U+03A6 ISOgrk3 -->
<!ENTITY Chi      "&#935;"> <!-- greek capital letter chi, U+03A7 -->
<!ENTITY Psi      "&#936;"> <!-- greek capital letter psi,
                                    U+03A8 ISOgrk3 -->
<!ENTITY Omega    "&#937;"> <!-- greek capital letter omega,
                                    U+03A9 ISOgrk3 -->

<!ENTITY alpha    "&#945;"> <!-- greek small letter alpha,
                                    U+03B1 ISOgrk3 -->
<!ENTITY beta     "&#946;"> <!-- greek small letter beta, U+03B2 ISOgrk3 -->
<!ENTITY gamma    "&#947;"> <!-- greek small letter gamma,
                                    U+03B3 ISOgrk3 -->
<!ENTITY delta    "&#948;"> <!-- greek small letter delta,
                                    U+03B4 ISOgrk3 -->
<!ENTITY epsilon  "&#949;"> <!-- greek small letter epsilon,
                                    U+03B5 ISOgrk3 -->
<!ENTITY zeta     "&#950;"> <!-- greek small letter zeta, U+03B6 ISOgrk3 -->
<!ENTITY eta      "&#951;"> <!-- greek small letter eta, U+03B7 ISOgrk3 -->
<!ENTITY theta    "&#952;"> <!-- greek small letter theta,
                                    U+03B8 ISOgrk3 -->
<!ENTITY iota     "&#953;"> <!-- greek small letter iota, U+03B9 ISOgrk3 -->
<!ENTITY kappa    "&#954;"> <!-- greek small letter kappa,
                                    U+03BA ISOgrk3 -->
<!ENTITY lambda   "&#955;"> <!-- greek small letter lambda,
                                    U+03BB ISOgrk3 -->
<!ENTITY mu       "&#956;"> <!-- greek small letter mu, U+03BC ISOgrk3 -->
<!ENTITY nu       "&#957;"> <!-- greek small letter nu, U+03BD ISOgrk3 -->
<!ENTITY xi       "&#958;"> <!-- greek small letter xi, U+03BE ISOgrk3 -->
<!ENTITY omicron  "&#959;"> <!-- greek small letter omicron, U+03BF NEW -->
<!ENTITY pi       "&#960;"> <!-- greek small letter pi, U+03C0 ISOgrk3 -->
<!ENTITY rho      "&#961;"> <!-- greek small letter rho, U+03C1 ISOgrk3 -->
<!ENTITY sigmaf   "&#962;"> <!-- greek small letter final sigma,
                                    U+03C2 ISOgrk3 -->
<!ENTITY sigma    "&#963;"> <!-- greek small letter sigma,
                                    U+03C3 ISOgrk3 -->
<!ENTITY tau      "&#964;"> <!-- greek small letter tau, U+03C4 ISOgrk3 -->
<!ENTITY upsilon  "&#965;"> <!-- greek small letter upsilon,
                                    U+03C5 ISOgrk3 -->
<!ENTITY phi      "&#966;"> <!-- greek small letter phi, U+03C6 ISOgrk3 -->
<!ENTITY chi      "&#967;"> <!-- greek small letter chi, U+03C7 ISOgrk3 -->
<!ENTITY psi      "&#968;"> <!-- greek small letter psi, U+03C8 ISOgrk3 -->
<!ENTITY omega    "&#969;"> <!-- greek small letter omega,
                                    U+03C9 ISOgrk3 -->
<!ENTITY thetasym "&#977;"> <!-- greek small letter theta symbol,
                                    U+03D1 NEW -->
<!ENTITY upsih    "&#978;"> <!-- greek upsilon with hook symbol,
                                    U+03D2 NEW -->
<!ENTITY piv      "&#982;"> <!-- greek pi symbol, U+03D6 ISOgrk3 -->

<!-- General Punctuation -->
<!ENTITY bull     "&#8226;"> <!-- bullet = black small circle,
                                     U+2022 ISOpub  -->
<!-- bullet is NOT the same as bullet operator, U+2219 -->
<!ENTITY hellip   "&#8230;"> <!-- horizontal ellipsis = three dot leader,
                                     U+2026 ISOpub  -->
<!ENTITY prime    "&#8242;"> <!-- prime = minutes = feet, U+2032 ISOtech -->
<!ENTITY Prime    "&#8243;"> <!-- double prime = seconds = inches,
                                     U+2033 ISOtech -->
<!ENTITY oline    "&#8254;"> <!-- overline = spacing overscore,
                                     U+203E NEW -->
<!ENTITY frasl    "&#8260;"> <!-- fraction slash, U+2044 NEW -->

<!-- Letterlike Symbols -->
<!ENTITY weierp   "&#8472;"> <!-- script capital P = power set
                                     = Weierstrass p, U+2118 ISOamso -->
<!ENTITY image    "&#8465;"> <!-- blackletter capital I = imaginary part,
                                     U+2111 ISOamso -->
<!ENTITY real     "&#8476;"> <!-- blackletter capital R = real part symbol,
                                     U+211C ISOamso -->
<!ENTITY trade    "&#8482;"> <!-- trade mark sign, U+2122 ISOnum -->
<!ENTITY alefsym  "&#8501;"> <!-- alef symbol = first transfinite cardinal,
                                     U+2135 NEW -->
<!-- alef symbol is NOT the same as hebrew letter alef,
     U+05D0 although the same glyph could be used to depict both characters -->

<!-- Arrows -->
<!ENTITY larr     "&#8592;"> <!-- leftwards arrow, U+2190 ISOnum -->
<!ENTITY uarr     "&#8593;"> <!-- upwards arrow, U+2191 ISOnum-->
<!ENTITY rarr     "&#8594;"> <!-- rightwards arrow, U+2192 ISOnum -->
<!ENTITY darr     "&#8595;"> <!-- downwards arrow, U+2193 ISOnum -->
<!ENTITY harr     "&#8596;"> <!-- left right arrow, U+2194 ISOamsa -->
<!ENTITY crarr    "&#8629;"> <!-- downwards arrow with corner leftwards
                                     = carriage return, U+21B5 NEW -->
<!ENTITY lArr     "&#8656;"> <!-- leftwards double arrow, U+21D0 ISOtech -->
<!-- ISO 10646 does not say that lArr is the same as the 'is implied by' arrow
    but also does not have any other character for that function. So ? lArr can
    be used for 'is implied by' as ISOtech suggests -->
<!ENTITY uArr     "&#8657;"> <!-- upwards double arrow, U+21D1 ISOamsa -->
<!ENTITY rArr     "&#8658;"> <!-- rightwards double arrow,
                                     U+21D2 ISOtech -->
<!-- ISO 10646 does not say this is the 'implies' character but does not have
     another character with this function so ?
     rArr can be used for 'implies' as ISOtech suggests -->
<!ENTITY dArr     "&#8659;"> <!-- downwards double arrow, U+21D3 ISOamsa -->
<!ENTITY hArr     "&#8660;"> <!-- left right double arrow,
                                     U+21D4 ISOamsa -->

<!-- Mathematical Operators -->
<!ENTITY forall   "&#8704;"> <!-- for all, U+2200 ISOtech -->
<!ENTITY part     "&#8706;"> <!-- partial differential, U+2202 ISOtech  -->
<!ENTITY exist    "&#8707;"> <!-- there exists, U+2203 ISOtech -->
<!ENTITY empty    "&#8709;"> <!-- empty set = null set = diameter,
                                     U+2205 ISOamso -->
<!ENTITY nabla    "&#8711;"> <!-- nabla = backward difference,
                                     U+2207 ISOtech -->
<!ENTITY isin     "&#8712;"> <!-- element of, U+2208 ISOtech -->
<!ENTITY notin    "&#8713;"> <!-- not an element of, U+2209 ISOtech -->
<!ENTITY ni       "&#8715;"> <!-- contains as member, U+220B ISOtech -->
<!-- should there be a more memorable name than 'ni'? -->
<!ENTITY prod     "&#8719;"> <!-- n-ary product = product sign,
                                     U+220F ISOamsb -->
<!-- prod is NOT the same character as U+03A0 'greek capital letter pi' though
     the same glyph might be used for both -->
<!ENTITY sum      "&#8721;"> <!-- n-ary sumation, U+2211 ISOamsb -->
<!-- sum is NOT the same character as U+03A3 'greek capital letter sigma'
     though the same glyph might be used for both -->
<!ENTITY minus    "&#8722;"> <!-- minus sign, U+2212 ISOtech -->
<!ENTITY lowast   "&#8727;"> <!-- asterisk operator, U+2217 ISOtech -->
<!ENTITY radic    "&#8730;"> <!-- square root = radical sign,
                                     U+221A ISOtech -->
<!ENTITY prop     "&#8733;"> <!-- proportional to, U+221D ISOtech -->
<!ENTITY infin    "&#8734;"> <!-- infinity, U+221E ISOtech -->
<!ENTITY ang      "&#8736;"> <!-- angle, U+2220 ISOamso -->
<!ENTITY and      "&#8743;"> <!-- logical and = wedge, U+2227 ISOtech -->
<!ENTITY or       "&#8744;"> <!-- logical or = vee, U+2228 ISOtech -->
<!ENTITY cap      "&#8745;"> <!-- intersection = cap, U+2229 ISOtech -->
<!ENTITY cup      "&#8746;"> <!-- union = cup, U+222A ISOtech -->
<!ENTITY int      "&#8747;"> <!-- integral, U+222B ISOtech -->
<!ENTITY there4   "&#8756;"> <!-- therefore, U+2234 ISOtech -->
<!ENTITY sim      "&#8764;"> <!-- tilde operator = varies with = similar to,
                                     U+223C ISOtech -->
<!-- tilde operator is NOT the same character as the tilde, U+007E,
     although the same glyph might be used to represent both  -->
<!ENTITY cong     "&#8773;"> <!-- approximately equal to, U+2245 ISOtech -->
<!ENTITY asymp    "&#8776;"> <!-- almost equal to = asymptotic to,
                                     U+2248 ISOamsr -->
<!ENTITY ne       "&#8800;"> <!-- not equal to, U+2260 ISOtech -->
<!ENTITY equiv    "&#8801;"> <!-- identical to, U+2261 ISOtech -->
<!ENTITY le       "&#8804;"> <!-- less-than or equal to, U+2264 ISOtech -->
<!ENTITY ge       "&#8805;"> <!-- greater-than or equal to,
                                     U+2265 ISOtech -->
<!ENTITY sub      "&#8834;"> <!-- subset of, U+2282 ISOtech -->
<!ENTITY sup      "&#8835;"> <!-- superset of, U+2283 ISOtech -->
<!-- note that nsup, 'not a superset of, U+2283' is not covered by the Symbol
     font encoding and is not included. Should it be, for symmetry?
     It is in ISOamsn  -->
<!ENTITY nsub     "&#8836;"> <!-- not a subset of, U+2284 ISOamsn -->
<!ENTITY sube     "&#8838;"> <!-- subset of or equal to, U+2286 ISOtech -->
<!ENTITY supe     "&#8839;"> <!-- superset of or equal to,
                                     U+2287 ISOtech -->
<!ENTITY oplus    "&#8853;"> <!-- circled plus = direct sum,
                                     U+2295 ISOamsb -->
<!ENTITY otimes   "&#8855;"> <!-- circled times = vector product,
                                     U+2297 ISOamsb -->
<!ENTITY perp     "&#8869;"> <!-- up tack = orthogonal to = perpendicular,
                                     U+22A5 ISOtech -->
<!ENTITY sdot     "&#8901;"> <!-- dot operator, U+22C5 ISOamsb -->
<!-- dot operator is NOT the same character as U+00B7 middle dot -->

<!-- Miscellaneous Technical -->
<!ENTITY lceil    "&#8968;"> <!-- left ceiling = apl upstile,
                                     U+2308 ISOamsc  -->
<!ENTITY rceil    "&#8969;"> <!-- right ceiling, U+2309 ISOamsc  -->
<!ENTITY lfloor   "&#8970;"> <!-- left floor = apl downstile,
                                     U+230A ISOamsc  -->
<!ENTITY rfloor   "&#8971;"> <!-- right floor, U+230B ISOamsc  -->
<!ENTITY lang     "&#9001;"> <!-- left-pointing angle bracket = bra,
                                     U+2329 ISOtech -->
<!-- lang is NOT the same character as U+003C 'less than'
     or U+2039 'single left-pointing angle quotation mark' -->
<!ENTITY rang     "&#9002;"> <!-- right-pointing angle bracket = ket,
                                     U+232A ISOtech -->
<!-- rang is NOT the same character as U+003E 'greater than'
     or U+203A 'single right-pointing angle quotation mark' -->

<!-- Geometric Shapes -->
<!ENTITY loz      "&#9674;"> <!-- lozenge, U+25CA ISOpub -->

<!-- Miscellaneous Symbols -->
<!ENTITY spades   "&#9824;"> <!-- black spade suit, U+2660 ISOpub -->
<!-- black here seems to mean filled as opposed to hollow -->
<!ENTITY clubs    "&#9827;"> <!-- black club suit = shamrock,
                                     U+2663 ISOpub -->
<!ENTITY hearts   "&#9829;"> <!-- black heart suit = valentine,
                                     U+2665 ISOpub -->
<!ENTITY diams    "&#9830;"> <!-- black diamond suit, U+2666 ISOpub -->

<!-- C0 Controls and Basic Latin -->
<!ENTITY quot    "&#34;"> <!-- quotation mark = APL quote,
                                    U+0022 ISOnum -->
<!ENTITY amp     "&#38;"> <!-- ampersand, U+0026 ISOnum -->
<!ENTITY lt      "&#60;"> <!-- less-than sign, U+003C ISOnum -->
<!ENTITY gt      "&#62;"> <!-- greater-than sign, U+003E ISOnum -->

<!-- Latin Extended-A -->
<!ENTITY OElig   "&#338;"> <!-- latin capital ligature OE,
                                    U+0152 ISOlat2 -->
<!ENTITY oelig   "&#339;"> <!-- latin small ligature oe, U+0153 ISOlat2 -->
<!-- ligature is a misnomer, this is a separate character in some languages -->
<!ENTITY Scaron  "&#352;"> <!-- latin capital letter S with caron,
                                    U+0160 ISOlat2 -->
<!ENTITY scaron  "&#353;"> <!-- latin small letter s with caron,
                                    U+0161 ISOlat2 -->
<!ENTITY Yuml    "&#376;"> <!-- latin capital letter Y with diaeresis,
                                    U+0178 ISOlat2 -->

<!-- Spacing Modifier Letters -->
<!ENTITY circ    "&#710;"> <!-- modifier letter circumflex accent,
                                    U+02C6 ISOpub -->
<!ENTITY tilde   "&#732;"> <!-- small tilde, U+02DC ISOdia -->

<!-- General Punctuation -->
<!ENTITY ensp    "&#8194;"> <!-- en space, U+2002 ISOpub -->
<!ENTITY emsp    "&#8195;"> <!-- em space, U+2003 ISOpub -->
<!ENTITY thinsp  "&#8201;"> <!-- thin space, U+2009 ISOpub -->
<!ENTITY zwnj    "&#8204;"> <!-- zero width non-joiner,
                                    U+200C NEW RFC 2070 -->
<!ENTITY zwj     "&#8205;"> <!-- zero width joiner, U+200D NEW RFC 2070 -->
<!ENTITY lrm     "&#8206;"> <!-- left-to-right mark, U+200E NEW RFC 2070 -->
<!ENTITY rlm     "&#8207;"> <!-- right-to-left mark, U+200F NEW RFC 2070 -->
<!ENTITY ndash   "&#8211;"> <!-- en dash, U+2013 ISOpub -->
<!ENTITY mdash   "&#8212;"> <!-- em dash, U+2014 ISOpub -->
<!ENTITY lsquo   "&#8216;"> <!-- left single quotation mark,
                                    U+2018 ISOnum -->
<!ENTITY rsquo   "&#8217;"> <!-- right single quotation mark,
                                    U+2019 ISOnum -->
<!ENTITY sbquo   "&#8218;"> <!-- single low-9 quotation mark, U+201A NEW -->
<!ENTITY ldquo   "&#8220;"> <!-- left double quotation mark,
                                    U+201C ISOnum -->
<!ENTITY rdquo   "&#8221;"> <!-- right double quotation mark,
                                    U+201D ISOnum -->
<!ENTITY bdquo   "&#8222;"> <!-- double low-9 quotation mark, U+201E NEW -->
<!ENTITY dagger  "&#8224;"> <!-- dagger, U+2020 ISOpub -->
<!ENTITY Dagger  "&#8225;"> <!-- double dagger, U+2021 ISOpub -->
<!ENTITY permil  "&#8240;"> <!-- per mille sign, U+2030 ISOtech -->
<!ENTITY lsaquo  "&#8249;"> <!-- single left-pointing angle quotation mark,
                                    U+2039 ISO proposed -->
<!-- lsaquo is proposed but not yet ISO standardized -->
<!ENTITY rsaquo  "&#8250;"> <!-- single right-pointing angle quotation mark,
                                    U+203A ISO proposed -->
<!-- rsaquo is proposed but not yet ISO standardized -->
<!ENTITY euro   "&#8364;"> <!-- euro sign, U+20AC NEW -->

]>
'''

class visitor(object):
    def do(self, tree):
        self.visit_node_list(tree.childNodes)

    def visit_node_list(self, nodelist):
        for node in nodelist:
            self.visit(node)

    def visit(self, node):
        nodeType = node.nodeType
        if node.nodeType == Node.ELEMENT_NODE:
            return self.visit_element(node)
        elif node.nodeType == Node.ATTRIBUTE_NODE:
            return self.visit_attribute(node)
        elif node.nodeType == Node.TEXT_NODE:
            return self.visit_text(node)
        elif node.nodeType == Node.CDATA_SECTION_NODE:
            return self.visit_cdata_section(node)

    def visit_element(self, node):
        if len(node.childNodes):
            self.visit_node_list(node.childNodes)

    def visit_attribute(self, node):
        pass

    def visit_text(self, node):
        pass

    def visit_cdata_section(self, node):
        pass


class strip_whitespace(visitor):

    def visit_element(self, node):
        if node.localName == 'p':
            # XXX: our formatter adds a whitespace at the end of each paragraph
            if node.hasChildNodes() and node.childNodes[-1].nodeType == Node.TEXT_NODE:
                data = node.childNodes[-1].data.rstrip('\n ')
                # Remove it if empty
                if data == '':
                    node.removeChild(node.childNodes[-1])
                else:
                    node.childNodes[-1].data = data
            # Remove empty paragraphs
            if not node.hasChildNodes():
                node.parentNode.removeChild(node)

        if node.hasChildNodes():
            self.visit_node_list(node.childNodes)


class convert_tree(visitor):
    white_space = object()
    new_line = object()
    new_line_dont_remove = object()

    def __init__(self, request, pagename):
        self.request = request
        self.pagename = pagename

    def do(self, tree):
        self.depth = 0
        self.text = []
        self.visit(tree.documentElement)
        self.check_whitespace()
        return ''.join(self.text)

    def check_whitespace(self):
        i = 0
        text = self.text
        while i < len(text):
            if text[i] is self.white_space:
                if i == 0 or i == len(text)-1:
                    del text[i]
                elif text[i-1].endswith(" ") or text[i-1].endswith("\n"):
                    # last char of previous element is whitespace
                    del text[i]
                elif (text[i+1] is self.white_space or
                      # next element is white_space
                      text[i+1] is self.new_line):
                      # or new_line
                    del text[i]
                elif text[i+1].startswith(" ") or text[i+1].startswith("\n"):
                    # first char of next element is whitespace
                    del text[i]
                else:
                    text[i] = " "
                    i += 1
            elif text[i] is self.new_line:
                if i == 0:
                    del text[i]
                elif i == len(text) - 1:
                    text[i] = "\n"
                    i += 1
                elif text[i-1].endswith("\n") or (
                      isinstance(text[i+1], str) and text[i+1].startswith("\n")):
                    del text[i]
                else:
                    text[i] = "\n"
                    i += 1
            elif text[i] is self.new_line_dont_remove:
                text[i] = "\n"
                i += 1
            else:
                i += 1

    def visit_text(self, node):
        self.text.append(node.data)

    def visit_element(self, node):
        name = node.localName
        if name is None: # not sure this can happen here (DOM comment node), but just for the case
            return
        func = getattr(self, "process_%s" % name, None)
        if func:
            func(node)
        else:
            self.process_inline(node)

    def visit_node_list_element_only(self, nodelist):
        for node in nodelist:
            if node.nodeType == Node.ELEMENT_NODE:
                self.visit_element(node)

    def node_list_text_only(self, nodelist):
        result = []
        for node in nodelist:
            if node.nodeType == Node.TEXT_NODE:
                result.append(node.data)
            else:
                result.extend(self.node_list_text_only(node.childNodes))
        return "".join(result)

    def get_desc(self, nodelist):
        """ links can have either text or an image as description - we extract
            this from the child nodelist and return wiki markup.
        """
        markup = ''
        text = self.node_list_text_only(nodelist).replace("\n", " ").strip()
        if text:
            # found some text
            markup = text
        else:
            # search for an img / object
            for node in nodelist:
                if node.nodeType == Node.ELEMENT_NODE:
                    name = node.localName
                    if name == 'img':
                        markup = self._process_img(node) # XXX problem: markup containts auto-generated alt text with link target
                        break
                    elif name == 'object':
                        markup = self._process_object(node)
                        break
        return markup

    def process_page(self, node):
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                self.visit_element(i)
            elif i.nodeType == Node.TEXT_NODE: # if this is missing, all std text under a headline is dropped!
                txt = i.data.strip() # IMPORTANT: don't leave this unstripped or there will be wrong blanks
                if txt:
                    self.text.append(txt)
            #we use <pre class="comment"> now, so this is currently unused:
            #elif i.nodeType == Node.COMMENT_NODE:
            #    self.text.append(i.data)
            #    self.text.append("\n")

    def process_br(self, node):
        self.text.append(self.new_line) # without this, std multi-line text below some heading misses a whitespace
                                        # when it gets merged to float text, like word word wordword word word

    def process_heading(self, node):
        text = self.node_list_text_only(node.childNodes).strip()
        if text:
            depth = int(node.localName[1])
            hstr = "=" * depth
            self.text.append(self.new_line)
            self.text.append("%s %s %s" % (hstr, text.replace("\n", " "), hstr))
            self.text.append(self.new_line)

    process_h1 = process_heading
    process_h2 = process_heading
    process_h3 = process_heading
    process_h4 = process_heading
    process_h5 = process_heading
    process_h6 = process_heading

    def _get_list_item_markup(self, list, listitem):
        before = ""
        #indent = str(self.depth) * self.depth # nice for debugging :)
        indent = " " * self.depth
        markup = ""
        name = list.localName
        if name == 'ol':
            class_ = listitem.getAttribute("class")
            if class_ == "gap":
                before = self.new_line_dont_remove
            if list.hasAttribute("type"):
                type = list.getAttribute("type")
            else:
                type = "1"
            markup = "%s. " % type
        elif name == 'ul':
            class_ = listitem.getAttribute("class")
            if class_ == "gap":
                before = self.new_line_dont_remove
            style = listitem.getAttribute("style")
            if re.match(ur"list-style-type:\s*none", style, re.I):
                markup = ". "
                # set markup with white space when list element containes table
                for i in listitem.childNodes:
                    if i.nodeType == Node.ELEMENT_NODE:
                        if i.localName == 'table':
                            markup = ""
            else:
                markup = "* "
        elif name == 'dl':
            markup = ":: "
        else:
            raise ConvertError("Illegal list type %s" % name)
        return before, indent, markup

    def process_dl(self, node):
        self.depth += 1
        markup = ":: " # can there be a dl dd without dt?
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                name = i.localName
                if name == 'dt':
                    before, indent, markup = self._get_list_item_markup(node, i)
                    self.text.extend([before, indent])
                    text = self.node_list_text_only(i.childNodes)
                    self.text.append(text.replace("\n", " "))
                elif name == 'dd':
                    self.text.append(markup)
                    self.process_list_item(i, indent) # XXX no dt -> indent is undefined!!!
                else:
                    raise ConvertError("Illegal list element %s" % i.localName)
        self.depth -= 1
        if self.depth == 0:
            self.text.append(self.new_line_dont_remove)

    def process_list(self, node):
        self.depth += 1
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                name = i.localName
                if name == 'li':
                    before, indent, markup = self._get_list_item_markup(node, i)
                    self.text.extend([before, indent, markup])
                    self.process_list_item(i, indent)
                elif name in ('ol', 'ul', ):
                    self.process_list(i)
                elif name == 'dl':
                    self.process_dl(i)
                else:
                    raise ConvertError("Illegal list element %s" % i.localName)
        self.depth -= 1
        if self.depth == 0:
            self.text.append(self.new_line_dont_remove)

    process_ul = process_list
    process_ol = process_list

    def empty_paragraph_queue(self, nodelist, indent, need_indent):
        if need_indent:
            self.text.append(indent)
        for i in nodelist:
            if i.nodeType == Node.ELEMENT_NODE:
                if i.localName == 'br':
                    self.text.append('<<BR>>')
                else:
                    self.process_inline(i)
            elif i.nodeType == Node.TEXT_NODE:
                self.text.append(i.data.strip('\n').replace('\n', ' '))
        self.text.append(self.new_line)
        del nodelist[:]

    def process_list_item(self, node, indent):
        found = False
        need_indent = False
        pending = []

        # If this is a empty list item, we just terminate the line
        if node.childNodes.length == 0:
            self.text.append(self.new_line)
            return

        for i in node.childNodes:
            name = i.localName

            if name in ('p', 'pre', 'ol', 'ul', 'dl', 'table', ) and pending:
                self.empty_paragraph_queue(pending, indent, need_indent)
                need_indent = True

            if name == 'p':
                if need_indent:
                    self.text.append(indent)
                self.process_paragraph_item(i)
                self.text.append(self.new_line)
                found = True
            elif name == 'pre':
                if need_indent:
                    self.text.append(indent)
                self.process_preformatted_item(i)
                found = True
            elif name in ('ol', 'ul', ):
                self.process_list(i)
                found = True
            elif name == 'dl':
                self.process_dl(i)
                found = True
            elif name == 'table':
                if need_indent:
                    self.text.append(indent)
                self.process_table(i)
                found = True
            elif name == 'br':
                pending.append(i)
            else:
                pending.append(i)

            if found:
                need_indent = True

        if pending:
            self.empty_paragraph_queue(pending, indent, need_indent)

    def process_blockquote(self, node):
        # XXX this does not really work. e.g.:
        # <bq>aaaaaa
        # <hr---------->
        # <bq>bbbbbb
        self.depth += 1
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                name = i.localName
                if name == 'p':
                    self.text.append(self.new_line)
                    self.text.append(" " * self.depth)
                    self.process_p(i)
                elif name == 'pre':
                    self.text.append(self.new_line)
                    self.text.append(" " * self.depth)
                    self.process_pre(i)
                elif name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', ):
                    self.process_heading(i)
                elif name in ('ol', 'ul', ):
                    self.process_list(i)
                elif name == 'dl':
                    self.process_dl(i)
                elif name == 'a':
                    self.process_a(i)
                elif name == 'img':
                    self.process_img(i)
                elif name == 'div':
                    self.visit_node_list_element_only(i.childNodes)
                elif name == 'blockquote':
                    self.process_blockquote(i)
                elif name == 'hr':
                    self.process_hr(i)
                elif name == 'br':
                    self.process_br(i)
                else:
                    raise ConvertError("process_blockquote: Don't support %s element" % name)
        self.depth -= 1

    def process_inline(self, node):
        if node.nodeType == Node.TEXT_NODE:
            self.text.append(node.data.strip('\n').replace('\n', ' '))
            return

        # do we need to check for Node.ELEMENT_NODE and return (do nothing)?
        name = node.localName # can be None for DOM Comment nodes
        if name is None:
            return

        # unsupported tags
        if name in (u'title', u'meta', u'style'):
            return

        if name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', ): # headers are not allowed here (e.g. inside a ul li),
            text = self.node_list_text_only(node.childNodes).strip() # but can be inserted via the editor
            self.text.append(text)                          # so we just drop the header markup and keep the text
            return

        func = getattr(self, "process_%s" % name, None)
        if func:
            func(node)
            return

        command_close = None
        if name in ('em', 'i', ):
            command = "''"
        elif name in ('strong', 'b', ):
            command = "'''"
        elif name == 'u':
            command = "__"
        elif name == 'big':
            command = "~+"
            command_close = "+~"
        elif name == 'small':
            command = "~-"
            command_close = "-~"
        elif name == 'strike':
            command = "--("
            command_close = ")--"
        elif name == 'sub':
            command = ",,"
        elif name == 'sup':
            command = "^"
        elif name in ('area', 'center', 'code', 'embed', 'fieldset', 'font', 'form', 'iframe', 'input', 'label', 'link', 'map',
                      'meta', 'noscript', 'option', 'script', 'select', 'textarea', 'wbr'):
            command = "" # just throw away unsupported elements
        else:
            raise ConvertError("process_inline: Don't support %s element" % name)

        self.text.append(command)
        for i in node.childNodes:
            # lonly childnodes checked if they are only 'br'
            if command and len(node.childNodes) == 1:
                # formatted br alone is not wanted (who wants a bold br?)
                if i.localName != 'br':
                    self.process_inline(i)
            else:
                if i.localName == 'br':
                    # dont make a real \n because that breaks tables
                    self.text.append('<<BR>>')
                else:
                    self.process_inline(i)
        if command_close:
            command = command_close
        self.text.append(command)

    def process_span(self, node):
        # process span tag for firefox3
        node_style = node.getAttribute("style")

        is_strike = node.getAttribute("class") == "strike"
        is_strike = is_strike or "line-through" in node_style
        is_strong = "bold" in node_style
        is_italic = "italic" in node_style
        is_underline = "underline" in node_style
        is_comment = node.getAttribute("class") == "comment"

        # start tag
        if is_comment:
            self.text.append("/* ")
        if is_strike:
            self.text.append("--(")
        if is_strong:
            self.text.append("'''")
        if is_italic:
            self.text.append("''")
        if is_underline:
            self.text.append("__")

        # body
        for i in node.childNodes:
            self.process_inline(i)

        # end tag
        if is_underline:
            self.text.append("__")
        if is_italic:
            self.text.append("''")
        if is_strong:
            self.text.append("'''")
        if is_strike:
            self.text.append(")--")
        if is_comment:
            self.text.append(" */")

    def process_div(self, node):
        # process indent
        self._process_indent(node)

        # ignore div tags - just descend
        for i in node.childNodes:
            self.visit(i)

    def process_tt(self, node):
        text = self.node_list_text_only(node.childNodes).replace("\n", " ")
        if node.getAttribute("class") == "backtick":
            self.text.append("`%s`" % text)
        else:
            self.text.append("{{{%s}}}" % text)

    def process_hr(self, node):
        if node.hasAttribute("class"):
            class_ = node.getAttribute("class")
        else:
            class_ = "hr0"
        if class_.startswith("hr") and class_[2] in "123456":
            length = int(class_[2]) + 4
        else:
            length = 4
        self.text.extend([self.new_line, "-" * length, self.new_line])

    def process_p(self, node):
        # process indent
        self._process_indent(node)
        self.process_paragraph_item(node)
        self.text.append("\n\n") # do not use self.new_line here!

    def _process_indent(self, node):
        # process indent
        node_style = node.getAttribute("style")
        match = re.match(r"margin-left:\s*(\d+)px", node_style)
        if match:
            left_margin = int(match.group(1))
            indent_depth = int(left_margin / 40)
            if indent_depth > 0:
                self.text.append(' . ')

    def process_paragraph_item(self, node):
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                self.process_inline(i)
            elif i.nodeType == Node.TEXT_NODE:
                self.text.append(i.data.strip('\n').replace('\n', ' '))

    def process_pre(self, node):
        self.process_preformatted_item(node)
        self.text.append(self.new_line)

    def process_preformatted_item(self, node):
        if node.hasAttribute("class"):
            class_ = node.getAttribute("class")
        else:
            class_ = None
        if class_ == "comment": # we currently use this for stuff like ## or #acl
            for i in node.childNodes:
                if i.nodeType == Node.TEXT_NODE:
                    self.text.append(i.data.replace('\n', ''))
                elif i.localName == 'br':
                    self.text.append(self.new_line)
                else:
                    pass
        else:
            content_buffer = []
            longest_inner_formater = ''
            bang_args = ''
            delimiters = []

            """
            below code fixed for MoinMoinBugs/GuiEditorCantNest bug
            this has problem when outer delimiter has two more { than inside one
            e.g. {{{{{{ {{{ foo }}} }}}}}}  --> {{{{ {{{ foo }}} }}}}
                   {{{foo {{{ }}} foo}}} --> {{{{ {{{ }}} }}}}
            """

            for i in node.childNodes:
                if i.nodeType == Node.TEXT_NODE:
                    # get longest pre tag({{{ or }}}) from content
                    delimiters.extend(re.compile("((?u){+)").findall(i.data))
                    delimiters.extend(re.compile("((?u)}+)").findall(i.data))
                    # when first line is empty, start iteration second line of i.data
                    data_lines = i.data.rstrip().split('\n')
                    if data_lines[0].strip() == '':
                        data_lines = data_lines[1:]
                    for line in data_lines:
                        if line.strip().startswith('#!'):
                            if bang_args == '':
                                bang_args = line.strip()
                            else:
                                content_buffer.extend([line, self.new_line])
                        else:
                            content_buffer.extend([line, self.new_line])
                elif i.localName == 'br':
                    content_buffer.append(self.new_line_dont_remove)
                else:
                    pass

            if delimiters:
                longest_inner_formater = max(delimiters)

            if (len(longest_inner_formater) >= 3):
                self.text.extend([("{" * (len(longest_inner_formater) + 1)) + bang_args, \
                                      self.new_line])
                self.text.extend(content_buffer)
                self.text.extend(["}" * (len(longest_inner_formater) + 1), \
                                      self.new_line])
            else:
                self.text.extend(["{{{"+bang_args, self.new_line])
                self.text.extend(content_buffer)
                self.text.extend(["}}}", self.new_line])

    _alignment = {"left": "(",
                  "center": ":",
                  "right": ")",
                  "top": "^",
                  "bottom": "v"}

    def _check_length(self, value):
        try:
            int(value)
            return value + 'px'
        except ValueError:
            return value

    def _get_color(self, node, prefix):
        if node.hasAttribute("bgcolor"):
            value = node.getAttribute("bgcolor")
            match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", value)
            if match:
                value = '#%X%X%X' % (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            else:
                match = re.match(r"#[0-9A-Fa-f]{6}", value)
            if not prefix and match:
                result = value
            else:
                result = '%sbgcolor="%s"' % (prefix, value)
        else:
            result = ''
        return result

    def _table_style(self, node):
        # TODO: attrs = get_attrs(node)
        result = []
        result.append(self._get_color(node, 'table'))
        if node.hasAttribute("width"):
            value = node.getAttribute("width")
            result.append('tablewidth="%s"' % self._check_length(value))
        if node.hasAttribute("height"):
            value = node.getAttribute("height")
            result.append('tableheight="%s"' % self._check_length(value))
        if node.hasAttribute("align"):
            value = node.getAttribute("align")
            result.append('tablealign="%s"' % value)
        if node.hasAttribute("style"):
            result.append('tablestyle="%s"' % node.getAttribute("style"))
        if node.hasAttribute("class"):
            result.append('tableclass="%s"' % node.getAttribute("class"))
        return " ".join(result).strip()

    def _row_style(self, node):
        # TODO: attrs = get_attrs(node)
        result = []
        result.append(self._get_color(node, 'row'))
        if node.hasAttribute("style"):
            result.append('rowstyle="%s"' % node.getAttribute("style"))
        if node.hasAttribute("class"):
            result.append('rowclass="%s"' % node.getAttribute("class"))
        return " ".join(result).strip()

    def _cell_style(self, node):
        # TODO: attrs = get_attrs(node)
        if node.hasAttribute("rowspan"):
            rowspan = ("|%s" % node.getAttribute("rowspan"))
        else:
            rowspan = ""

        if node.hasAttribute("colspan"):
            colspan = int(node.getAttribute("colspan"))
        else:
            colspan = 1

        spanning = rowspan or colspan > 1

        align = ""
        result = []
        result.append(self._get_color(node, ''))
        if node.hasAttribute("align"):
            value = node.getAttribute("align")
            if not spanning or value != "center":
                # ignore "center" in spanning cells
                align += self._alignment.get(value, "")
        if node.hasAttribute("valign"):
            value = node.getAttribute("valign")
            if not spanning or value != "center":
                # ignore "center" in spanning cells
                align += self._alignment.get(value, "")
        if node.hasAttribute("width"):
            value = node.getAttribute("width")
            if value[-1] == "%":
                align += value
            else:
                result.append('width="%s"' % self._check_length(value))
        if node.hasAttribute("height"):
            value = node.getAttribute("height")
            result.append('height="%s"' % self._check_length(value))
        if node.hasAttribute("class"):
            result.append('class="%s"' % node.getAttribute("class"))
        if node.hasAttribute("id"):
            result.append('id="%s"' % node.getAttribute("id"))
        if node.hasAttribute("style"):
            result.append('style="%s"' % node.getAttribute("style"))

        if align:
            result.insert(0, "%s" % align)
        result.append(rowspan)
        return " ".join(result).strip()

    def process_table(self, node, style=""):
        if self.depth == 0:
            self.text.append(self.new_line)
        self.new_table = True
        style += self._table_style(node)
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                name = i.localName
                if name == 'tr':
                    self.process_table_record(i, style)
                    style = ""
                elif name in ('thead', 'tbody', 'tfoot'):
                    self.process_table(i, style)
                elif name == 'caption':
                    self.process_caption(node, i, style)
                    style = ''
                elif name in ('col', 'colgroup', 'strong', ):
                    pass # we don't support these, but we just ignore them
                else:
                    raise ConvertError("process_table: Don't support %s element" % name)
            #else:
            #    raise ConvertError("Unexpected node: %r" % i)
        self.text.append(self.new_line_dont_remove)

    def process_caption(self, table, node, style=""):
        # get first row
        for i in table.childNodes:
            if i.localName in ('thead', 'tbody', 'tfoot'): # XXX is this correct?
            #if i.localName == 'tbody': (old version)
                for i in i.childNodes:
                    if i.localName == 'tr':
                        break
                break
            elif i.localName == 'tr':
                break
        # count columns
        if i.localName == 'tr':
            colspan = 0
            for td in i.childNodes:
                if not td.nodeType == Node.ELEMENT_NODE:
                    continue
                span = td.getAttribute('colspan')
                try:
                    colspan += int(span)
                except ValueError:
                    colspan += 1
        else:
            colspan = 1
        text = self.node_list_text_only(node.childNodes).replace('\n', ' ').strip()
        if text:
            if style:
                style = '<%s>' % style
            self.text.extend(["%s%s'''%s'''||" % ('||' * colspan, style, text), self.new_line_dont_remove])

    def process_table_data(self, node, style=""):
        if node.hasAttribute("colspan"):
            colspan = int(node.getAttribute("colspan"))
        else:
            colspan = 1
        self.text.append("||" * colspan)

        style += self._cell_style(node)
        if style:
            self.text.append("<%s>" % style)

        found = False
        for i in node.childNodes:
            name = i.localName
            if name == 'p':
                self.process_paragraph_item(i)
                self.text.append(self.white_space)
                found = True
        if not found:
            for i in node.childNodes:
                name = i.localName
                if i.nodeType == Node.ELEMENT_NODE:
                    if name == 'br':
                        # if we get a br for a cell from e.g. cut and paste from OOo
                        # or if someone simulates a list by enter in a cell
                        # it should be appended as macro BR.
                        self.text.append('<<BR>>')
                        found = True
                        continue
                    else:
                        self.process_inline(i)
                        found = True
                elif i.nodeType == Node.TEXT_NODE:
                    data = i.data.strip('\n').replace('\n', ' ')
                    if data:
                        found = True
                        self.text.append(data)
        if not found:
            self.text.append(" ")

    def process_table_record(self, node, style=""):
        if not self.new_table:
            self.text.append(" " * self.depth)
        else:
            self.new_table = False
        style += self._row_style(node)
        for i in node.childNodes:
            if i.nodeType == Node.ELEMENT_NODE:
                name = i.localName
                if name in ('td', 'th', ):
                    self.process_table_data(i, style=style)
                    style = ""
                else:
                    raise ConvertError("process_table_record: Don't support %s element" % name)
        self.text.extend(["||", self.new_line_dont_remove])

    def process_a(self, node):
        attrs = get_attrs(node)

        title = attrs.pop('title', '')
        href = attrs.pop('href', None)
        css_class = attrs.get('class')

        scriptname = self.request.getScriptname()
        if scriptname == "":
            scriptname = "/"

        # can either be a link (with href) or an anchor (with e.g. id)
        # we don't need to support anchors here as we currently handle them as <<Anchor(id)>> macro
        if href:
            href = wikiutil.url_unquote(href)

            interwikiname = None
            desc = self.get_desc(node.childNodes)

            # interwiki link
            if css_class == "interwiki":
                wikitag, wikiurl, wikitail, err = wikiutil.resolve_interwiki(
                    self.request, title, "") # the title has the wiki name, page = ""
                if not err and href.startswith(wikiurl):
                    pagename = wikiutil.url_unquote(href[len(wikiurl):].lstrip('/'))
                    interwikiname = "%s:%s" % (wikitag, pagename)
                else:
                    raise ConvertError("Invalid InterWiki link: '%s'" % href)
            elif css_class == "badinterwiki" and title:
                if href == "/": # we used this as replacement for empty href
                    href = ""
                pagename = wikiutil.url_unquote(href)
                interwikiname = "%s:%s" % (title, pagename)
            if interwikiname and pagename == desc:
                if interwiki_re.match(interwikiname+' '): # the blank is needed by interwiki_re to match
                    # this is valid as a free interwiki link
                    self.text.append("%s" % interwikiname)
                else:
                    self.text.append("[[%s]]" % interwikiname)
                return
            elif title == 'Self':
                self.text.append('[[%s|%s]]' % (href, desc))
                return
            elif interwikiname:
                self.text.append("[[%s|%s]]" % (interwikiname, desc))
                return

            # fix links generated by a broken copy & paste of gecko based browsers
            brokenness = '../../../..'
            if href.startswith(brokenness):
                href = href[len(brokenness):] # just strip it away!
            # TODO: IE pastes complete http://server/Page/SubPage as href and as text, too

            # Attachments
            if title.startswith("attachment:"):
                attname = wikiutil.url_unquote(title[len("attachment:"):])
                if 'do=get' in href: # quick&dirty fix for not dropping &do=get param
                    parms = '|&do=get'
                else:
                    parms = ''
                if attname != desc:
                    desc = '|%s' % desc
                elif parms:
                    desc = '|'
                else:
                    desc = ''
                self.text.append('[[attachment:%s%s%s]]' % (attname, desc, parms))
            # wiki link
            elif href.startswith(scriptname):
                pagename = href[len(scriptname):]
                pagename = pagename.lstrip('/')    # XXX temp fix for generated pagenames starting with /
                if desc == pagename:
                    self.text.append(wikiutil.pagelinkmarkup(pagename))
                # relative link /SubPage
                elif desc.startswith('/') and href.endswith(desc):
                    if pagename.startswith(self.pagename): # is this a subpage of us?
                        self.text.append(wikiutil.pagelinkmarkup(pagename[len(self.pagename):]))
                    else:
                        self.text.append(wikiutil.pagelinkmarkup(pagename))
                # relative link ../
                elif desc.startswith('../') and href.endswith(desc[3:]):
                    self.text.append(wikiutil.pagelinkmarkup(desc))
                # internal link #internal
                elif '#' in href and pagename.startswith(self.pagename):
                    self.text.append(wikiutil.pagelinkmarkup(href[href.index('#'):], desc))
                # labeled link
                else:
                    self.text.append(wikiutil.pagelinkmarkup(pagename, desc))
            # mailto link
            elif href.startswith("mailto:"):
                if href == desc or href[len("mailto:"):] == desc:
                    self.text.extend([self.white_space, desc, self.white_space])
                else:
                    self.text.append("[[%s|%s]]" % (href, desc)) # XXX use a (renamed) pagelinkmarkup
            # link
            else:
                if href == desc:
                    href = href.replace(" ", "%20")
                    self.text.append(href)
                else:
                    href = href.replace(" ", "%20")
                    if desc:
                        desc = '|' + desc
                    self.text.append("[[%s%s]]" % (href, desc))

    def process_img(self, node):
        markup = self._process_img(node)
        self.text.extend([self.white_space, markup, self.white_space])

    def _process_img(self, node):
        attrs = get_attrs(node)

        title = attrs.pop('title', '')
        if title.startswith("smiley:"):
            markup = title[len("smiley:"):]
            return markup

        alt = attrs.pop('alt', None)
        src = attrs.pop('src', None)
        css_class = attrs.get('class')

        target = src
        if title.startswith("attachment:"):
            target = wikiutil.url_unquote(title)
            if alt == title[len("attachment:"):]:
                # kill auto-generated alt
                alt = None
        elif title.startswith("drawing:"):
            target = wikiutil.url_unquote(title)
            if alt == title[len("drawing:"):]:
                # kill auto-generated alt
                alt = None
        else:
            if css_class == 'external_image':
                # kill auto-generated alt and class
                if src == alt:
                    alt = None
                del attrs['class']

        if alt:
            desc = '|' + alt
        else:
            desc = ''

        params = ','.join(['%s="%s"' % (k, v) for k, v in attrs.items()])
                           # if k in ('width', 'height', )])
        if params:
            params = '|' + params
            if not desc:
                desc = '|'

        markup = "{{%s%s%s}}" % (target, desc, params)
        return markup

    def process_object(self, node):
        markup = self._process_object(node)
        self.text.append(markup)

    def _process_object(self, node):
        attrs = get_attrs(node)
        markup = ''
        data = attrs.pop('data', None)
        if data:
            data = wikiutil.url_unquote(data)

            desc = self.get_desc(node.childNodes)
            if desc:
                desc = '|' + desc

            params = ','.join(['%s="%s"' % (k, v) for k, v in attrs.items()])
                               # if k in ('width', 'height', )])
            if params:
                params = '|' + params
                if not desc:
                    desc = '|'
            markup = "{{%s%s%s}}" % (data, desc, params)
        return markup
        # TODO: for target PAGES, use some code from process_a to get the pagename from URL
        # TODO: roundtrip attachment: correctly
        # TODO: handle object's content better?

def get_attrs(node):
    """ get the attributes of <node> into an easy-to-use dict """
    attrs = {}
    for attr_name in node.attributes.keys():
        # get attributes of style element
        if attr_name == "style":
            for style_element in node.attributes.get(attr_name).nodeValue.split(';'):
                if style_element.strip() != '':
                    style_elements = style_element.split(':')
                    if len(style_elements) == 2:
                        attrs[style_elements[0].strip()] = style_elements[1].strip()
        # get attributes without style element
        else:
            attrs[attr_name] = node.attributes.get(attr_name).nodeValue
    return attrs


def parse(request, text):
    text = u'<?xml version="1.0"?>%s%s' % (dtd, text)
    text = text.encode(config.charset)
    try:
        return xml.dom.minidom.parseString(text)
    except xml.parsers.expat.ExpatError, msg:
        # this sometimes crashes when it should not, so save the stuff to analyze it:
        logname = os.path.join(request.cfg.data_dir, "expaterror.log")
        f = file(logname, "w")
        f.write(text)
        f.write("\n" + "-"*80 + "\n" + str(msg))
        f.close()
        raise ConvertError('ExpatError: %s (see dump in %s)' % (msg, logname))

def convert(request, pagename, text):
    # Due to expat needing explicitly set namespaces, we set these here to allow pasting
    # from Word / Excel without issues.
    # If you encounter 'ExpatError: unbound prefix', try adding the namespace to the list.
    namespace = [u'xmlns:o="urn:schemas-microsoft-com:office:office"',
                 u'xmlns:x="urn:schemas-microsoft-com:office:excel"',
                 u'xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"',
                 u'xmlns:c="urn:schemas-microsoft-com:office:component:spreadsheet"',
                 u'xmlns:s="uuid:BDC6E3F0-6DA3-11d1-A2A3-00AA00C14882"',
                 u'xmlns:dt="uuid:C2F41010-65B3-11d1-A29F-00AA00C14882"',
                 u'xmlns:rs="urn:schemas-microsoft-com:rowset"',
                 u'xmlns:z="#RowsetSchema"',
                 u'xmlns:x2="http://schemas.microsoft.com/office/excel/2003/xml"',
                 u'xmlns:sl="http://schemas.microsoft.com/schemaLibrary/2003/core"',
                 u'xmlns:aml="http://schemas.microsoft.com/aml/2001/core"',
                 u'xmlns:w="http://schemas.microsoft.com/office/word/2003/wordml"',
                 u'xmlns:wx="http://schemas.microsoft.com/office/word/2003/auxHint"',
                 u'xmlns:w10="urn:schemas-microsoft-com:office:word"',
                 u'xmlns:v="urn:schemas-microsoft-com:office:vml"']
    text = u'<page %s>%s</page>' % (' '.join(namespace), text)
    tree = parse(request, text)
    strip_whitespace().do(tree)
    text = convert_tree(request, pagename).do(tree)
    text = '\n'.join([s.rstrip() for s in text.splitlines()] + ['']) # remove trailing blanks
    return text

