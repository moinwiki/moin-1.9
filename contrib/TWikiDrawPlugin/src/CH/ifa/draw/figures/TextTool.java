/*
 * @(#)TextTool.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.awt.event.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.util.FloatingTextField;

/**
 * Tool to create new or edit existing text figures.
 * The editing behavior is implemented by overlaying the
 * Figure providing the text with a FloatingTextField.<p>
 * A tool interaction is done once a Figure that is not
 * a TextHolder is clicked.
 *
 * @see TextHolder
 * @see FloatingTextField
 */
public class TextTool extends CreationTool {

    private FloatingTextField   fTextField;
    private TextHolder  fTypingTarget;

    public TextTool(DrawingView view, Figure prototype) {
        super(view, prototype);
    }

    /**
     * If the pressed figure is a TextHolder it can be edited otherwise
     * a new text figure is created.
     */
    public void mouseDown(MouseEvent e, int x, int y)
    {
	    Figure pressedFigure;
	    TextHolder textHolder = null;

	    pressedFigure = drawing().findFigureInside(x, y);
	    if (pressedFigure instanceof TextHolder) {
	        textHolder = (TextHolder) pressedFigure;
	        if (!textHolder.acceptsTyping())
	            textHolder = null;
        }
	    if (textHolder != null) {
	        beginEdit(textHolder);
	        return;
	    }
	    if (fTypingTarget != null) {
	        editor().toolDone();
	        endEdit();
	    } else {
    	    super.mouseDown(e, x, y);
    	    textHolder = (TextHolder)createdFigure();
    	    beginEdit(textHolder);
        }
    }

    public void mouseDrag(MouseEvent e, int x, int y) {
    }

    public void mouseUp(MouseEvent e, int x, int y) {
    }

    /**
     * Terminates the editing of a text figure.
     */
    public void deactivate() {
        super.deactivate();
        endEdit();
    }

    /**
     * Sets the text cursor.
     */
    public void activate() {
        super.activate();
        view().clearSelection();
        // JDK1.1 TEXT_CURSOR has an incorrect hot spot
        //view.setCursor(Cursor.getPredefinedCursor(Cursor.TEXT_CURSOR));
    }

    protected void beginEdit(TextHolder figure) {
        if (fTextField == null)
            fTextField = new FloatingTextField();

	if (figure != fTypingTarget && fTypingTarget != null)
	    endEdit();

        fTextField.createOverlay((Container)view(), figure.getFont());
	fTextField.setBounds(fieldBounds(figure), figure.getText());
	fTypingTarget = figure;
    }

    protected void endEdit() {
	if (fTypingTarget != null) {
	    if (fTextField.getText().length() > 0)
		fTypingTarget.setText(fTextField.getText());
	    else
		drawing().remove((Figure)fTypingTarget);
	    fTypingTarget = null;
	    fTextField.endOverlay();
	    view().checkDamage();
	}
    }

    private Rectangle fieldBounds(TextHolder figure) {
    	Rectangle box = figure.textDisplayBox();
    	int nRows = figure.overlayRows();
    	int nCols = figure.overlayColumns();
        Dimension d = fTextField.getPreferredSize(nRows, nCols);
        return new Rectangle(box.x, box.y, d.width, d.height);
    }
}

