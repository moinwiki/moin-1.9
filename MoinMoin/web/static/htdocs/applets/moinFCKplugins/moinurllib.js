/* -------------------- UTF-8 encoder ------------------------- */
function encode_utf8(t)
{
  // dient der Normalisierung des Zeilenumbruchs
  var d=[];
  for(var n=0; n<t.length; n++)
  {
    var c=t.charCodeAt(n);
    // all the signs of ansi => 1byte
    if (c<128)
       d[d.length]= c;
    // all the signs between 127 and 2047 => 2byte
    else if((c>127) && (c<2048)) 
    {
      d[d.length]= ((c>>6)|192);
      d[d.length]= ((c&63)|128);
    }
    // all the signs between 2048 and 66536 => 3byte
    else 
    {
      d[d.length]= ((c>>12)|224);
      d[d.length]= (((c>>6)&63)|128);
      d[d.length]= ((c&63)|128);
    }
  }
  for (var n=0; n<d.length; n++)
    d[n] = String.fromCharCode(d[n]);
  return d.join("");
}

/* -------------------- UTF-8 decoder ------------------------- */
function decode_utf8(d)
{
  var r=[]; var i=0;
  var c=c1=c2=0;
  while(i<d.length)
  {
    c = d.charCodeAt(i);
    if (c<128) 
    {
       r[r.length]= String.fromCharCode(c); 
       i++;
    }
    else if((c>191) && (c<224)) 
    {
      c1 = d.charCodeAt(i+1); 
      r[r.length]= String.fromCharCode(((c&31)<<6) | (c1&63)); 
      i+=2;
    }
    else 
    {
      c2 = d.charCodeAt(i+2);
      r[r.length]= String.fromCharCode(((c&15)<<12) | ((c1&63)<<6) | (c2&63));
      i+=3;
    }
  }
  return r.join("");
}

function hex_to_char(string)
{
 return String.fromCharCode(parseInt(string.substring(1,3), 16));
}

var sHex = "0123456789ABCDEF"

function char_to_hex(string)
{
  var iChar = string.charCodeAt(0);
  return '%' + sHex.charAt((iChar>>4)&15) + sHex.charAt(iChar&15);
}

function decodeUrl(url)
{
  url = url.replace(/%../g , hex_to_char);
  return decode_utf8(url);
}

function encodeUrl(url)
{ 
  url = encode_utf8(url);
  return url.replace(/[^a-zA-Z\/.:]/g, char_to_hex);
}

