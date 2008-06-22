function showObj(title, obj)
{ // show an object in a alert box
  var res = '';
  res += title+': '+obj+'\n\n';
  for (temp in obj)
  {
    res += temp+': '+obj[temp]+', ';
  }
  res += '\n';
  alert(res);
}

// --------------------------------

if (FCK.EditorWindow.getSelection) // Gecko
{ 
  // assume exactly one selection
  
  FCKSelection.GetStartNode = function()
    {
      var oSelection = FCK.EditorWindow.getSelection();
      var oContainer = oSelection.getRangeAt(0).startContainer;
      var iOffset = oSelection.getRangeAt(0).startOffset;
      if (oContainer.childNodes.length>iOffset) 
        return oContainer.childNodes[iOffset];
      else
        return oContainer;
        
    }
  // only valid if GetStartNode() returns text node
  FCKSelection.GetStartOffset = function()
    {
      var oSelection = FCK.EditorWindow.getSelection();
      return oSelection.getRangeAt(0).startOffset;    
    }
  FCKSelection.GetEndNode = function()
    {
      var oSelection = FCK.EditorWindow.getSelection();
      var oContainer = oSelection.getRangeAt(0).endContainer;
      var iOffset = oSelection.getRangeAt(0).startEndset;
      if (oContainer.childNodes.length>iOffset) 
        return oContainer.childNodes[iOffset];
      else
        return oContainer;

    }
  // only valid if GetEndNode() returns text node
  FCKSelection.GetEndOffset = function()
    {
      var oSelection = FCK.EditorWindow.getSelection();
      return oSelection.getRangeAt(0).endOffset;    
    }
  FCKSelection.IsCollapsed = function()
    {
      var oSelection = FCK.EditorWindow.getSelection();
      return oSelection.getRangeAt(0).collapsed;    
    }
  FCKSelection.GetText = function()
    {
      return FCK.EditorWindow.getSelection().toString();
    }
}
/* ##########################################################################
 * ###   IE 
 * #########################################################################
 */
else if (FCK.EditorDocument.selection)
{

  function invalidSelection()
    {
      FCKSelection._startNode = null;
      FCKSelection._endNode = null;
    }

  FCK.AttachToOnSelectionChange(invalidSelection);

  FCKSelection._startNode = null;
  FCKSelection._endNode = null;

  FCKSelection.GetStartNode = function()
    {
      if (!FCKSelection._startNode) 
      {
	FCKSelection._startNode = FCKSelection._getStartNode()
      }
      return FCKSelection._startNode;
    }


  FCKSelection._getStartNode = function()
    {
      if (FCKSelection._startNode) return FCKSelection._startNode;
      var oRange = FCK.EditorDocument.selection.createRange();
      if (FCKSelection.GetType()=="Control")
      {
        return oRange.item(0);
      }
      else // Text, None
      {
        var oTmpRange = FCK.EditorDocument.selection.createRange();
        var parent = oRange.parentElement();
        var oNode = null;
	var following_text = 0;
        if (!parent.hasChildNodes()) 
          return parent; // selection in empty tag
        oNode = parent.firstChild;
        var oLastText = oNode;
        while (oNode)
        {
          if (oNode.nodeName!="#text") 
            {
	      following_text = false;
              oTmpRange.moveToElementText(oNode);
              if (oRange.compareEndPoints('StartToEnd', oTmpRange)<0)
                {
                  // found
                  if (oRange.compareEndPoints('StartToStart', oTmpRange)<=0)
                    return oLastText; // already inside selection
                  oNode = oNode.firstChild;
                }
              else
                oNode = oNode.nextSibling;
            }
          else
            {
	      if (!following_text)
		{
		  oLastText = oNode;
		  following_text = true;
		}
              try {
                 oNode = oNode.nextSibling;
              }
              catch (e) {
		if (parent.childNodes.length>=2)
		  oNode = parent.childNodes[1];
		else
		  return parent;
		  
                 // alert(e);
                 //showObj('parent', parent);
		 //showObj('node', oNode);
                 // showObj('childNodes[0]', parent.childNodes[0]);
                 //oNode = false;
              }
            }
        }
        return oLastText;
      }
    }

  FCKSelection.GetStartOffset = function() 
    {
      // XXX does not work yet!
      var oNode = FCKSelection.GetStartNode();
      if (oNode.nodeType!=3) return 0; // not a text node 
      var startoffset = 0;
      var selrange = FCK.EditorDocument.selection.createRange();
      var elrange = selrange.duplicate();
      if (oNode.previousSilbing)
      {
        elrange.moveToElementText(oNode.previousSibling);
        while (selrange.compareEndPoints('StartToEnd', elrange) > 0) 
          {
            startoffset++;
            elrange.moveEnd('character', 1);
          }
      }
      else
      { 
        elrange.moveToElementText(oNode.parentNode);
        while (selrange.compareEndPoints('StartToStart', elrange) > 0) 
          {
            startoffset++;
            elrange.moveStart('character', 1);
          }
      }
      return startoffset;
    }

  FCKSelection.GetEndNode = function()
    {
      if (!FCKSelection._endNode) 
      {
	FCKSelection._endNode = FCKSelection._getEndNode()
      }
      return FCKSelection._endNode;
    }

  FCKSelection._getEndNode = function()
    {
      FCKSelection.sEnd = "";
      var oRange = FCK.EditorDocument.selection.createRange();
      if (FCKSelection.GetType()=="Control")
      {
        return oRange.item(oRange.length-1);
      }
      else // Text, None
      {
        var oTmpRange = FCK.EditorDocument.selection.createRange();
        var oNode = oRange.parentElement()
	var following_text = false;
        if (!oNode.hasChildNodes()) return oNode; // selection in empty tag
        oNode = oNode.lastChild;
        var oLastText = oNode;
        while (oNode)
        {
          if (oNode.nodeName!="#text") 
            {
	      following_text = false;
              oTmpRange.moveToElementText(oNode);
              if (oRange.compareEndPoints('EndToStart', oTmpRange)>0)
                {
                  if (oRange.compareEndPoints('EndToEnd', oTmpRange)>=0)
                    return oLastText; // already in selection
                  // found
                  FCKSelection.sEnd += oNode.nodeName + "->";
                  oNode = oNode.lastChild;
                  if (oNode) FCKSelection.sEnd += oNode.nodeName + ";";
                  
                }
              else
                oNode = oNode.previousSibling;
            }
          else
            {
	      if (!following_text)
		{
		  oLastText = oNode;
		  following_text = true;
		}
              try{
                oNode = oNode.previousSibling;
              } catch (e) {
                return oRange.parentElement();
              }
            }
        }
        return oLastText;
      }
    }

  FCKSelection.GetEndOffset = function() 
    {
      // XXX does not work yet!
      var oNode = FCKSelection.GetEndNode();
      if (oNode.nodeType!=3) return 0; // not a text node 
      var endoffset = 0;
      var selrange = FCK.EditorDocument.selection.createRange();
      var elrange = selrange.duplicate();
      if (oNode.nextSilbing)
      {
        elrange.moveToElementText(oNode.nextSibling);
        while (selrange.compareEndPoints('EndToStart', elrange) < 0) 
          {
            endoffset++;
            elrange.moveStart('character', -1);
          }
      }      
      else 
      {
        elrange.moveToElementText(oNode.parentNode);
        while (selrange.compareEndPoints('EndToEnd', elrange) < 0) 
        {
          endoffset++;
          elrange.moveStart('character', -11);
        }
      }
      return endoffset;
    }


  FCKSelection.GetText = function()
    {
      var oRange = FCK.EditorDocument.selection.createRange();
      return oRange.text;
    }
  FCKSelection.IsCollapsed = function()
    {
      return FCKSelection.GetType()=='None';
    }
}

/* 
 * Checks if the name of any of the selected nodes or the nodes surrounding 
 * the selection match the pattern RE.
 * Returns FCK_TRISTATE_DISABLED insted of true.
 */

var sAlert = "";

var Alert = function(sText)
{
  if (sText!=sAlert)
  {
    sAlert = sText;
    alert(sText);
  }
}

FCKSelection.CheckForNodeNames = function(pattern)
{
  var oStart = FCKSelection.GetStartNode();
  var oEnd = FCKSelection.GetEndNode();

  if (!oStart){
    //Alert("No Start");
    return 0;
  }
  if (!oEnd){
    //Alert("No End");
    return 0;
  }
  
  /* Crashes IE
  if ((FCKSelection.GetType()=="None") && (oStart!=oEnd))
  {
    FCKSelection.GetParentElement().normalize();
    var oStart = FCKSelection.GetStartNode();
    var oEnd = FCKSelection.GetEndNode();
  }
  */

  // Check surrounding nodes
  var oElement = oStart;
  while (oElement)
  {
    if (pattern.test(oElement.nodeName))
      { 
        //Alert("Start:" + oStart.nodeName + ':' + oElement.nodeName + 
        //      ':' + oEnd.nodeName);
        return FCK_TRISTATE_DISABLED;
      }
    oElement = oElement.parentNode;
  }
  oElement = oEnd;
  while (oElement)
  {
    if (pattern.test(oElement.nodeName))
      { 
        //Alert("End:" + oStart.nodeName + ':' + oElement.nodeName + 
        //      ':' + oEnd.nodeName);
        return FCK_TRISTATE_DISABLED;
      }
    oElement = oElement.parentNode;
  }

  if (FCKSelection.IsCollapsed()) 
  {
    return 0;
  }
  // check selected nodes
  var oNode = oStart;

  while (oNode)
  {
    if (pattern.test(oNode.nodeName))
      {
        //Alert("Down:" + oStart.nodeName + ':' + oNode.nodeName + ':' + 
        //      oEnd.nodeName + FCKSelection.GetStartOffset() + ":" +
        //      FCKSelection.GetEndOffset());
        
        return FCK_TRISTATE_DISABLED;
      }
    if (oNode==oEnd && oNode!=oStart)
    {
      return 0;
    }
    if (oNode.hasChildNodes()) 
    {
      oNode = oNode.firstChild;
    }
    else
    {
      if (oNode==oEnd) return 0; // happens if oStart==oEnd && no children
      while (!oNode.nextSibling) 
      {
        oNode = oNode.parentNode;
        if (!oNode) return 0;
        if (pattern.test(oNode.nodeName))
          {
            //Alert("Up:" + oStart.nodeName +':'+ oNode.nodeName + ':' + 
            //          oEnd.nodeName);
            return FCK_TRISTATE_DISABLED;
          }
        if (oNode==oEnd) return 0;
      }
      oNode = oNode.nextSibling;
    }
  }
  return 0;
}
