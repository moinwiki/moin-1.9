var word_rule = RegExp(FCKConfig['WordRule']);

var MoinUnlink = function(){}

MoinUnlink.prototype = new FCKNamedCommand('Unlink');

MoinUnlink.prototype.Execute = function()
{
  /*
  // code for selection debugging
  if (0) 
  {
    var oStart = FCKSelection.GetStartNode()
    var sStart = ""
    var oEnd = FCKSelection.GetEndNode()
    var sEnd = "";
    var sSame = (oStart==oEnd) ? "Same:" : "different";
    
    while (oStart)
    {
      sStart += oStart.nodeName + ">";
      oStart = oStart.parentNode;
    }
    while (oEnd)
    {
      sEnd += oEnd.nodeName + ">";
      oEnd = oEnd.parentNode;
    }

    alert(//FCKSelection.GetParentElement().nodeName+':'+
	  sSame +
	  sStart + '|||' + sEnd + ":" +
	  //FCKSelection.GetStartOffset() + ':' +
	  //FCKSelection.GetEndOffset() + ':' +
	  "Collapsed:" + FCKSelection.IsCollapsed() + ':' +
	  "Type:" + FCKSelection.GetType());
    return
  }
  */

  if(FCKSelection.GetType()=='Control')
  {
    FCK.ExecuteNamedCommand('Unlink');
  }
  else //if (FCK.GetNamedCommandState("Unlink")==FCK_TRISTATE_ON)
  {
    if (FCKSelection.IsCollapsed()) 
    {
      FCKSelection.SelectNode(FCKSelection.MoveToAncestorNode('A'));
    }

    var sText = FCKSelection.GetText();

    FCK.ExecuteNamedCommand('Unlink');
    FCKSelection.Collapse();

    if (word_rule.test(sText))
    {
      FCK.InsertHtml('<span style="background-color:#ffff11">!</span>');
    }
  }
}

//MoinUnlink.prototype.GetState = function(){return FCK_TRISTATE_OFF}

FCKCommands.RegisterCommand('Unlink', new MoinUnlink());
