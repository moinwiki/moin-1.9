/*
 * Created on 12-Feb-2005
 *
 * TODO To change the template for this generated file go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
package com.wombatinvasion.pmwikidraw;

import java.awt.event.MouseEvent;

import org.jhotdraw.contrib.AttributeLineFigure;
import org.jhotdraw.figures.PolyLineFigure;
import org.jhotdraw.framework.DrawingEditor;
import org.jhotdraw.framework.Figure;
import org.jhotdraw.standard.AbstractTool;
import org.jhotdraw.standard.PasteCommand;
import org.jhotdraw.standard.SingleFigureEnumerator;
import org.jhotdraw.util.Undoable;

/**
 * @author bob
 *
 * TODO To change the template for this generated type comment go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
public class PmWikiScribbleTool extends AbstractTool {

	
	private AttributeLineFigure fScribble;
	private int             fLastX, fLastY;
	/**
	 * the figure that was actually added
	 * Note, this can be a different figure from the one which has been created.
	 */
	private Figure myAddedFigure;
	private final boolean freeHandMode;
	/**
	 * @param newDrawingEditor
	 */
	public PmWikiScribbleTool(DrawingEditor newDrawingEditor, boolean freehand) {
		super(newDrawingEditor);
		freeHandMode = freehand;
	}
	/**
	 * @param newDrawingEditor
	 */
	public PmWikiScribbleTool(DrawingEditor newDrawingEditor) {
		this(newDrawingEditor, false);
	}
	
	public void mouseUp(MouseEvent e, int x, int y) {
		if(freeHandMode ) 
		{
			deactivate();
		} 
		else 
		{
			if (e.getClickCount() >= 2) 
			{
				editor().toolDone();
			}
		}
	}

	public void activate() {
		super.activate();
	}

	public void deactivate() {
		super.deactivate();
		if (fScribble != null) {
		  if(!freeHandMode) {
				if (fScribble.size().width < 4 || fScribble.size().height < 4) {
					getActiveDrawing().remove(fScribble);
					// nothing to undo
					setUndoActivity(null);
				}
		  }
			fScribble = null;
		}
	}

	private void point(int x, int y) {
		if (fScribble == null) {
			fScribble = new AttributeLineFigure(new PolyLineFigure(x, y));
			setAddedFigure(view().add(fScribble));
		}
		else if (fLastX != x || fLastY != y) {
			fScribble.addPoint(x, y);
		}

		fLastX = x;
		fLastY = y;
	}

	public void mouseDown(MouseEvent e, int x, int y) {
		super.mouseDown(e,x,y);

		if (e.getClickCount() >= 2) {
			// use undo activity from paste command...
			setUndoActivity(createUndoActivity());

			// put created figure into a figure enumeration
			getUndoActivity().setAffectedFigures(new SingleFigureEnumerator(getAddedFigure()));
		}
		else {
			// use original event coordinates to avoid
			// supress that the scribble is constrained to
			// the grid [when in freeHandMode]
			if(freeHandMode) {
				point(e.getX(), e.getY());
			}
			else 
			{ 
				point(x, y);
			}
		}
	}

	public void mouseDrag(MouseEvent e, int x, int y) {
		if (fScribble != null) {
			if(freeHandMode) {
				point(e.getX(), e.getY());
			}
			else 
			{ 
				point(x, y);
			}
		}
	}

	/**
	 * Gets the figure that was actually added
	 * Note, this can be a different figure from the one which has been created.
	 */
	protected Figure getAddedFigure() {
		return myAddedFigure;
	}

	private void setAddedFigure(Figure newAddedFigure) {
		myAddedFigure = newAddedFigure;
	}

	/**
	 * Factory method for undo activity
	 */
	protected Undoable createUndoActivity() {
		return new PasteCommand.UndoActivity(view());
	}
}
