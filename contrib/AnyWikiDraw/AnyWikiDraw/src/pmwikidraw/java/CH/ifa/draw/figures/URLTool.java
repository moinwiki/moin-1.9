/*
 * @(#)URLTool.java 5.1
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
public class URLTool extends CreationTool {
  
  private FloatingTextField   fTextField;
  private Figure  fTypingTarget;
  private static Font dialogFont = Font.decode("dialog-PLAIN-12");
  
  public URLTool(DrawingView view, Figure prototype) {
    super(view, prototype);
  }
  
  /**
   * If the pressed figure is a TextHolder it can be edited otherwise
   * a new text figure is created.
   */
  public void mouseDown(MouseEvent e, int x, int y)
  {
    Figure pressedFigure;
    
    pressedFigure = drawing().findFigureInside(x, y);
    if (pressedFigure != null) {
      beginEdit(pressedFigure);
    } else if (fTypingTarget != null) {
      editor().toolDone();
      endEdit();
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
  
  protected void beginEdit(Figure figure) {
    if (fTextField == null)
      fTextField = new FloatingTextField(1, 25);
    
    if (figure != fTypingTarget && fTypingTarget != null)
      endEdit();
    
    fTextField.createOverlay((Container)view(), dialogFont);
    fTextField.setBounds(fieldBounds(figure), (String)figure.getAttribute("Sensitive"));
    
    fTypingTarget = figure;
  }
  
  protected void endEdit() {
    if (fTypingTarget != null) {
      fTypingTarget.setAttribute("Sensitive", fTextField.getText());
      fTypingTarget = null;
      fTextField.endOverlay();
      view().checkDamage();
    }
  }
  
  private Rectangle fieldBounds(Figure figure) {
    Rectangle box = figure.displayBox();
    Dimension d = fTextField.getPreferredSize(1, 25);
    int middleX = box.x + ( (box.width/2) - (d.width/2) );
    int middleY = box.y + ( (box.height/2) - (d.height/2) );
    return new Rectangle(middleX, middleY, d.width, d.height);
  }
}

