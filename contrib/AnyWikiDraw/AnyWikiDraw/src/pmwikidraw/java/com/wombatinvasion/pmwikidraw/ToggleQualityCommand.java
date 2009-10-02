/*
 * Created on 28-Nov-2004
 *
 * TODO To change the template for this generated file go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
package com.wombatinvasion.pmwikidraw;

import org.jhotdraw.framework.DrawingChangeEvent;
import org.jhotdraw.framework.DrawingEditor;
import org.jhotdraw.framework.Figure;
import org.jhotdraw.framework.FigureChangeEvent;
import org.jhotdraw.framework.FigureEnumeration;
import org.jhotdraw.standard.AbstractCommand;

/**
 * @author bob
 *
 * TODO To change the template for this generated type comment go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
public class ToggleQualityCommand extends AbstractCommand {

	/**
	 * @param newName
	 * @param newDrawingEditor
	 */
	public ToggleQualityCommand(String newName, DrawingEditor newDrawingEditor) {
		super(newName, newDrawingEditor, true);
		
	}

	/* (non-Javadoc)
	 * @see org.jhotdraw.standard.AbstractCommand#execute()
	 */
	public void execute() {
		super.execute();
		((PmWikiDrawingView)view()).setQualityMode(!((PmWikiDrawingView)view()).getQualityMode());
		FigureEnumeration fe = view().drawing().figures();
		while(fe.hasNextFigure()) {
			fe.nextFigure().invalidate();
		}
		view().drawingRequestUpdate(new DrawingChangeEvent(view().drawing(), null));
	}
}
