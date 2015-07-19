// debug function.
// TODO : make common javascript class and extract this one
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



/**
 * range usage is different on each browser
 * internet explorer use Microsoft Text Range and others use W3C Range
 * 
 * follow link describe that
 * http://www.quirksmode.org/dom/range_intro.html#t00
 *
 * because of this reason getting something on selected node is divided 2 part
 * first for internet explorer and second for others
 * each codes implement same function do same behavior
 * to understand following code. it's better others part first.
 * it's more easy and short
 */


// --------------------------------
// IE
// --------------------------------
if (sSuffix == 'ie') {
  // initialize startNode and endNode
  function invalidSelection()
  {
      FCKSelection._startNode = null;
      FCKSelection._endNode = null;
  }

  // everytime selection changed. initialize internal variables 
  FCK.AttachToOnSelectionChange(invalidSelection);

  FCKSelection._startNode = null;
  FCKSelection._endNode = null;


  // get start node of seleced element
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

    var oRange = FCKSelection.GetSelection().createRange();

    if (FCKSelection.GetType()=="Control")
    {
      return oRange.item(0);
    }
    else // Text, None
    {
      var oTmpRange = FCKSelection.GetSelection().createRange();
      var parent = oRange.parentElement();
      var oNode = null;
      var following_text = 0;

      // selection in empty tag
      if ( !parent.hasChildNodes() ) 
        return parent; 

      // the first child of the parent of the selection
      oNode = parent.firstChild;
      var oLastText = oNode;

      // looping all lower nodes of the parent of selected object
      // and compare it with first selected node 
      // if oNode is not a text compare start of oRange and end of oTmpRange
      // and then compare start of both range(oRange, oTmpRange)
      while (oNode)
      {
        if (oNode.nodeName != "#text") 
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
          {
            oNode = oNode.nextSibling;
          }
        }
        else // oNode.nodeName == '#text'
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
            {
              oNode = parent.childNodes[1];
            }
            else 
            {
              return parent;
            }
          } // end of catch
        } // end of else
      } // end of while
      return oLastText;
    } // end of else
  }

  // getting start node offset
  FCKSelection.GetStartOffset = function() 
  {
    // XXX does not work yet!
    var oNode = FCKSelection.GetStartNode();
    
    // not a text node 
    if (oNode.nodeType != 3) 
      return 0; 

    var startoffset = 0;
    var selrange = FCKSelection.GetSelection().createRange();
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

  // get end node of seleced element
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
    var oRange = FCKSelection.GetSelection().createRange();

    if (FCKSelection.GetType()=="Control")
    {
      return oRange.item(oRange.length-1);
    }
    else // Text, None
    {
      var oTmpRange = FCKSelection.GetSelection().createRange();
      var oNode = oRange.parentElement()
      var following_text = false;

      // selection in empty tag
      if (!oNode.hasChildNodes()) 
        return oNode; 

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

            if (oNode) 
              FCKSelection.sEnd += oNode.nodeName + ";";
          }
          else 
          {
            oNode = oNode.previousSibling;
          }
        }
        else
        {
          if (!following_text)
          {
            oLastText = oNode;
            following_text = true;
          }

          try
          {
            oNode = oNode.previousSibling;
          } 
          catch (e) 
          {
            return oRange.parentElement();
          } // end of catch
        } // end of else
      } // end of while
      return oLastText;
    } // end of else
  } // end of function


  // getting offset of end node
  FCKSelection.GetEndOffset = function() 
  {
    var oNode = FCKSelection.GetEndNode();

    // not a text node 
    if (oNode.nodeType != 3)
      return 0; 

    var endoffset = 0;
    var selrange = FCKSelection.GetSelection().createRange();
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

  // return selected node's text
  FCKSelection.GetText = function()
  {
    var oRange = FCKSelection.GetSelection().createRange();
    return oRange.text;
  }

  // return true if selected node's type is None
  FCKSelection.IsCollapsed = function()
  {
    return FCKSelection.GetType() == 'None';
  }
}
// --------------------------------
// Others (firefox, safari, opera, ..)
// --------------------------------
else {
  // assume exactly one selection. only first selection accepted.
  FCKSelection.GetStartNode = function()
    {
      var oSelection = FCKSelection.GetSelection();
      if (oSelection.rangeCount == 0) // this fixes Chrome Browser exception on FCKeditor init
        return null;
      // startContainer returns the parent of the first node in the selection
      var oContainer = oSelection.getRangeAt(0).startContainer;
      // The offset within the startContainer where the range starts
      var iOffset = oSelection.getRangeAt(0).startOffset;

      // if oContainer has children return child at iOffset
      // otherwise return oContainer
      if (oContainer.childNodes.length > iOffset) 
        return oContainer.childNodes[iOffset];
      else
        return oContainer;
    }

  FCKSelection.GetStartOffset = function()
  {
    var oSelection = FCKSelection.GetSelection();
    return oSelection.getRangeAt(0).startOffset;
  }

  FCKSelection.GetEndNode = function()
  {
    var oSelection = FCKSelection.GetSelection();
    if (oSelection.rangeCount == 0) // this fixes Chrome Browser exception on FCKeditor init
      return null;
    var oContainer = oSelection.getRangeAt(0).endContainer;
    var iOffset = oSelection.getRangeAt(0).startEndset;

    if (oContainer.childNodes.length>iOffset) 
      return oContainer.childNodes[iOffset];
    else
      return oContainer;
  }

  FCKSelection.GetEndOffset = function()
  {
    var oSelection = FCKSelection.GetSelection();
    return oSelection.getRangeAt(0).endOffset;    
  }

  FCKSelection.IsCollapsed = function()
  {
    var oSelection = FCKSelection.GetSelection();
    return oSelection.getRangeAt(0).collapsed;
  }

  FCKSelection.GetText = function()
  {
    return FCKSelection.GetSelection().toString();
  }
}



// this function make toolbar's button enable/disable using inserted pattern.
// check coverage contains its parent and children.
FCKSelection.CheckForNodeNames = function(pattern)
{
  var oStart = FCKSelection.GetStartNode();
  var oEnd = FCKSelection.GetEndNode();

  // filtering invalid input and selection
  if (!oStart || !oEnd || !pattern){
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
      /*
      Alert("Down:" + oStart.nodeName + ':' + oNode.nodeName + ':' + 
            oEnd.nodeName + FCKSelection.GetStartOffset() + ":" +
            FCKSelection.GetEndOffset());
      */
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
      // happens if oStart==oEnd && no children
      if (oNode==oEnd) 
        return 0; 

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
