package com.wombatinvasion.pmwikidraw;

import java.awt.Color;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Hashtable;
import java.util.List;
import java.util.Vector;

import javax.swing.JColorChooser;
import javax.swing.JDialog;

import org.jhotdraw.figures.AttributeFigure;
import org.jhotdraw.figures.GroupFigure;
import org.jhotdraw.framework.DrawingEditor;
import org.jhotdraw.framework.DrawingView;
import org.jhotdraw.framework.Figure;
import org.jhotdraw.framework.FigureAttributeConstant;
import org.jhotdraw.framework.FigureEnumeration;
import org.jhotdraw.standard.AbstractCommand;
import org.jhotdraw.standard.ChangeAttributeCommand;
import org.jhotdraw.standard.CompositeFigure;
import org.jhotdraw.standard.FigureEnumerator;
import org.jhotdraw.standard.StandardFigureSelection;
import org.jhotdraw.util.CollectionsFactory;
import org.jhotdraw.util.ColorMap;
import org.jhotdraw.util.Undoable;
import org.jhotdraw.util.UndoableAdapter;
/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2004</p>
 * @author Ciaran Jessup
 * @version 1.0
 */

/*
 *  Modified:
 *   22-Nov-2004	cj       Initial development
 */

//------------------------------------------------------------------------------
/**
 * ColorPaletteChangeAttributeCommand
 */
public class ColorPaletteChangeAttributeCommand extends AbstractCommand
{
	private FigureAttributeConstant fAttribute;
	private Object fValue = null;
	private final String fTitle;
  private final JDialog chooserDlg;
  private final JColorChooser chooserPanel;
  private boolean fColorSelected = false; 
  /**
   * @param name
   * @param attribute
   * @param newDrawingEditor
   */
  public ColorPaletteChangeAttributeCommand(String name, FigureAttributeConstant attribute, DrawingEditor newDrawingEditor)
  {
    super(name, newDrawingEditor);
    fAttribute = attribute;
    fTitle = name;
    chooserPanel = new JColorChooser();
    chooserDlg = JColorChooser.createDialog(null,fTitle, true,chooserPanel,  
      new ActionListener() {
	      /* (non-Javadoc)
	       * @see java.awt.event.ActionListener#actionPerformed(java.awt.event.ActionEvent)
	     */
	      public void actionPerformed(ActionEvent arg0)
	      {
	        fColorSelected = true;
	      }
    	}, 
    	new ActionListener() {
    	  /* (non-Javadoc)
         * @see java.awt.event.ActionListener#actionPerformed(java.awt.event.ActionEvent)
         */
        public void actionPerformed(ActionEvent arg0)
        {
	        fColorSelected = false;
        }
    	});
  }
  
  /* (non-Javadoc)
   * @see org.jhotdraw.standard.ChangeAttributeCommand#execute()
   */
  public void execute()
  {
    super.execute();
    Color defaultColour = null;
    if ( !onlyChangeMode ) {
		FigureEnumeration figures = (FigureEnumeration)view().selection();
		if(figures.hasNextFigure()) { 
		  Figure figure = figures.nextFigure();
		  defaultColour = (Color) figure.getAttribute(fAttribute);
		}
		if(defaultColour == null) {
		  defaultColour = Color.black;
		}
		fColorSelected = false;
		
        chooserPanel.setColor(defaultColour);
        chooserDlg.show(true);
        fValue = chooserPanel.getColor();
    }
    else {
    	fColorSelected = true;
		fValue = AttributeFigure.getDefaultAttribute(fAttribute);
    }
    
    if(fColorSelected) {
			setUndoActivity(createUndoActivity());
			getUndoActivity().setAffectedFigures(view().selection());
      
			FigureEnumeration fe = getUndoActivity().getAffectedFigures();
			while (fe.hasNextFigure()) {
				Figure fig = fe.nextFigure();
				fig.setAttribute(fAttribute, fValue);
			}
			view().checkDamage();
      
      // Set the default colour
			AttributeFigure.setDefaultAttribute(fAttribute.getName() ,fValue);
    }
  }
  
	/**
	 * Factory method for undo activity
	 */
	protected Undoable createUndoActivity() {
		return new ColorPaletteChangeAttributeCommand.UndoActivity(view(), fAttribute, fValue);
	}

	public static class UndoActivity extends UndoableAdapter {
		private FigureAttributeConstant myUndoAttribute;
		private Hashtable	            myOriginalValues;
		private Object                  myUndoValue;

		public UndoActivity(DrawingView newDrawingView, FigureAttributeConstant newUndoAttribute, Object newUndoValue) {
			super(newDrawingView);
			myOriginalValues = new Hashtable();
			setAttribute(newUndoAttribute);
			setBackupValue(newUndoValue);
			setUndoable(true);
			setRedoable(true);
		}

		public boolean undo() {
			if (!super.undo()) {
				return false;
			}

			FigureEnumeration fe = getAffectedFigures();
			while (fe.hasNextFigure()) {
				Figure f = fe.nextFigure();
				if (getOriginalValue(f) != null) {
					f.setAttribute(getAttribute(), getOriginalValue(f));
				}
        else {
          f.setAttribute(getAttribute(), null);
        }
			}

			return true;
		}

		public boolean redo() {
			if (!isRedoable()) {
				return false;
			}

			FigureEnumeration fe = getAffectedFigures();
			while (fe.hasNextFigure()) {
				Figure f = fe.nextFigure();
				if (getBackupValue() != null) {
					f.setAttribute(getAttribute(), getBackupValue());
				}
			}

			return true;
		}

		protected void addOriginalValue(Figure affectedFigure, Object newOriginalValue) {
			myOriginalValues.put(affectedFigure, newOriginalValue);
		}

		protected Object getOriginalValue(Figure lookupAffectedFigure) {
			return myOriginalValues.get(lookupAffectedFigure);
		}

		protected void setAttribute(FigureAttributeConstant newUndoAttribute) {
			myUndoAttribute = newUndoAttribute;
		}

		public FigureAttributeConstant getAttribute() {
			return myUndoAttribute;
		}

		protected void setBackupValue(Object newUndoValue) {
			myUndoValue = newUndoValue;
		}

		public Object getBackupValue() {
			return myUndoValue;
		}

		public void release() {
			super.release();
			myOriginalValues = null;
		}

    private void flattenFigureEnumeration(FigureEnumeration fe, List figures) {
      
      while(fe.hasNextFigure()) {
        Figure fig = fe.nextFigure();
        if( !( fig instanceof CompositeFigure ) ) {
          figures.add(fig);
        }
        else {
          flattenFigureEnumeration( ((CompositeFigure)fig).figures(), figures );
        }
      }
    }

    private FigureEnumeration flattenFigureEnumeration(FigureEnumeration fe) {
      // Take a standard FE, extract the groups, and flatten out all the group elements
      List myRealFigureList = new Vector();
      flattenFigureEnumeration(fe, myRealFigureList);
      return new FigureEnumerator(myRealFigureList);
    }
    
		public void setAffectedFigures(FigureEnumeration fe) {
      FigureEnumeration useFe = flattenFigureEnumeration(fe);
      
			// first make copy of FigureEnumeration in superclass
			super.setAffectedFigures(useFe);
			// then get new FigureEnumeration of copy to save attributes
			FigureEnumeration copyFe = getAffectedFigures();
			while (copyFe.hasNextFigure()) {
				Figure f = copyFe.nextFigure();
        if ( f instanceof AttributeFigure ) {
				  Object attributeValue = ((AttributeFigure)f).getAttribute(getAttribute());
				  if (attributeValue != null) {
 					  addOriginalValue(f, attributeValue);
	 			  }
        }
			}
		}
	}
	
	private boolean onlyChangeMode = false;
	/**
	 * @param b
	 */
	public void setOnlyChangeMode(boolean b) {
		onlyChangeMode = b;
		
	}
}
