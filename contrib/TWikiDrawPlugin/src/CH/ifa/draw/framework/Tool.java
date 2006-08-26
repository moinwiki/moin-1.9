/*
 * @(#)Tool.java 5.1
 *
 */

package CH.ifa.draw.framework;

import java.awt.*;
import java.awt.event.MouseEvent;
import java.awt.event.KeyEvent;

/**
 * A tool defines a mode of the drawing view. All input events
 * targeted to the drawing view are forwarded to its current tool.<p>
 * Tools inform their editor when they are done with an interaction
 * by calling the editor's toolDone() method.
 * The Tools are created once and reused. They
 * are initialized/deinitialized with activate()/deactivate().
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld032.htm>State</a></b><br>
 * Tool plays the role of the State. In encapsulates all state
 * specific behavior. DrawingView plays the role of the StateContext.
 * @see DrawingView
 */

public interface Tool {

    /**
     * Activates the tool for the given view. This method is called
     * whenever the user switches to this tool. Use this method to
     * reinitialize a tool.
     */
    public void activate();

    /**
     * Deactivates the tool. This method is called whenever the user
     * switches to another tool. Use this method to do some clean-up
     * when the tool is switched. Subclassers should always call
     * super.deactivate.
     */
    public void deactivate();

    /**
     * Handles mouse down events in the drawing view.
     */
    public void mouseDown(MouseEvent e, int x, int y);

    /**
     * Handles mouse drag events in the drawing view.
     */
    public void mouseDrag(MouseEvent e, int x, int y);

    /**
     * Handles mouse up in the drawing view.
     */
    public void mouseUp(MouseEvent e, int x, int y);

    /**
     * Handles mouse moves (if the mouse button is up).
     */
    public void mouseMove(MouseEvent evt, int x, int y);

    /**
     * Handles key down events in the drawing view.
     */
    public void keyDown(KeyEvent evt, int key);
}
