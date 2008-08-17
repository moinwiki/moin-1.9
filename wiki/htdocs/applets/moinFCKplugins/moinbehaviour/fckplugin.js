
/* ###########################################################################
 * IE functions
 * ###########################################################################
 */

function Doc_OnKeyDown_IE()
{
  var e = FCK.EditorWindow.event;
  if (e.keyCode == 13) // ENTER
  {
    if (e.ctrlKey || e.altKey || e.shiftKey|| !FCKSelection.HasAncestorNode("PRE")) {
      return true;
    }
    else
    { 
      FCKSelection.Delete();
      var oTmpNode = FCK.CreateElement("B");
      oTmpNode.innerHTML = "&nbsp;";
      if (oTmpNode.previousSibling && oTmpNode.previousSibling.nodeType==3)
      {
        oTmpNode.previousSibling.nodeValue = 
      oTmpNode.previousSibling.nodeValue + '\r';
      }
      else
      {
        var oTxt = FCK.EditorDocument.createTextNode('\r');
        oTmpNode.parentNode.insertBefore(oTxt, oTmpNode);
      }
      var oRange = FCK.EditorDocument.selection.createRange();
      oRange.moveToElementText(oTmpNode);
      oRange.select();
      FCK.EditorDocument.selection.clear();	      
      return false;
    }
  }
  return true;
}


function Doc_OnKeyUp_IE()
{
  /*
  var e = FCK.EditorWindow.event;
  if (e.keyCode == 8 || e.keyCode==46) // backspace, delete
    {
  */
  var oNode = FCKSelection.GetParentElement();
  var siHTML = oNode.innerHTML;

  if (siHTML.search(/&nbsp;/i)!=-1)
  {
    oNode.normalize();
    alert("DING");
  }
      //    }
}
/* ##########################################################################
 * Register event handlers
 * ##########################################################################
 */

/*
// TODO FCK.EditorDocument is seems like deprecated, find alternative method for replace
if (FCK.EditorDocument.attachEvent) // IE
{
  FCK.EditorDocument.attachEvent('onkeydown', Doc_OnKeyDown_IE);
  //FCK.AttachToOnSelectionChange(Doc_OnKeyUp_IE);

}

*/