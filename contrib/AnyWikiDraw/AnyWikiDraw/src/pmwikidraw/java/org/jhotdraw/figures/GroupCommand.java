/*
 * @(#)GroupCommand.java
 *
 * Project:		JHotdraw - a GUI framework for technical drawings
 *				http://www.jhotdraw.org
 *				http://jhotdraw.sourceforge.net
 * Copyright:	© by the original author(s) and all contributors
 * License:		Lesser GNU Public License (LGPL)
 *				http://www.opensource.org/licenses/lgpl-license.html
 */

package org.jhotdraw.figures;

import org.jhotdraw.framework.*;
import org.jhotdraw.standard.*;
import org.jhotdraw.util.*;

import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.ListIterator;

/**
 * Command to group the selection into a GroupFigure.
 *
 * @see GroupFigure
 *
 * @version <$CURRENT_VERSION$>
 */
public  class GroupCommand extends AbstractCommand {

   /**
	 * Constructs a group command.
	 * @param name the command name
	 * @param newDrawingEditor the DrawingEditor which manages the views
	 */
	public GroupCommand(String name, DrawingEditor newDrawingEditor) {
		super(name, newDrawingEditor);
	}

	public void execute() {
		super.execute();
		setUndoActivity(createUndoActivity());
        FigureEnumeration figEnum =  view().selection();

        // CJ Sort figures by depth
        List sortedFigures = CollectionsFactory.current().createList();
        while(figEnum.hasNextFigure()) {
       	   sortedFigures.add(figEnum.nextFigure());
        }
        Collections.sort(sortedFigures, new FigureZIndexComparator());
    
		getUndoActivity().setAffectedFigures(new FigureEnumerator(sortedFigures));
		((GroupCommand.UndoActivity)getUndoActivity()).groupFigures();
		view().checkDamage();
	}

	public boolean isExecutableWithView() {
		return view().selectionCount() > 1;
	}

	/**
	 * Factory method for undo activity
	 */
	protected Undoable createUndoActivity() {
		return new GroupCommand.UndoActivity(view());
	}
	public class FigureZIndexComparator
	implements java.util.Comparator {
	  public int compare(Object o1, Object o2) {
	    int zIndex1 = ((Figure)o1).getZValue();
	    int zIndex2 = ((Figure)o2).getZValue();
	    return zIndex1-zIndex2;
	  }
	}
	public static class UndoActivity extends UndoableAdapter {
		public UndoActivity(DrawingView newDrawingView) {
			super(newDrawingView);
			setUndoable(true);
			setRedoable(true);
		}

		public boolean undo() {
			if (!super.undo()) {
				return false;
			}

			getDrawingView().clearSelection();

			// orphan group figure(s)
			getDrawingView().drawing().orphanAll(getAffectedFigures());

     
			// create a new collection with the grouped figures as elements
			List affectedFigures = CollectionsFactory.current().createList();

			FigureEnumeration fe = getAffectedFigures();
			while (fe.hasNextFigure()) {
				Figure currentFigure = fe.nextFigure();
				// add contained figures
				getDrawingView().drawing().addAll(currentFigure.figures());
				getDrawingView().addToSelectionAll(currentFigure.figures());

				FigureEnumeration groupedFigures = currentFigure.figures();
				while (groupedFigures.hasNextFigure()) {
					affectedFigures.add(groupedFigures.nextFigure());
				}
			}

			setAffectedFigures(new FigureEnumerator(affectedFigures));

			return true;
		}

		public boolean redo() {
			// do not call execute directly as the selection might has changed
			if (isRedoable()) {
				groupFigures();
				return true;
			}

			return false;
		}

		public void groupFigures() {
			getDrawingView().drawing().orphanAll(getAffectedFigures());
			getDrawingView().clearSelection();

			// add new group figure instead
			GroupFigure group = new GroupFigure();
			group.addAll(getAffectedFigures());

			Figure figure = getDrawingView().drawing().add(group);
			getDrawingView().addToSelection(figure);

			// create a new collection with the new group figure as element
			List affectedFigures = CollectionsFactory.current().createList();
			affectedFigures.add(figure);
			setAffectedFigures(new FigureEnumerator(affectedFigures));
		}
	}
}
