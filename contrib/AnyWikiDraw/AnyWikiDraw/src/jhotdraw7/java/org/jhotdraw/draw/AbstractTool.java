/*
 * @(#)AbstractTool.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.draw;

import javax.swing.*;
import org.jhotdraw.app.action.*;
import org.jhotdraw.beans.AbstractBean;
import org.jhotdraw.draw.action.*;
import java.awt.*;
import java.awt.geom.*;
import java.awt.event.*;
import javax.swing.event.*;

/**
 * This abstract class can be extended to implement a {@link Tool}.
 * 
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Proxy</em><br>
 * To remove the need for null-handling, {@code AbstractTool} makes use of
 * a proxy for {@code DrawingEditor}.
 * Subject: {@link DrawingEditor}; Proxy: {@link DrawingEditorProxy};
 * Client: {@link AbstractTool}.
 * <hr>
 *
 * @author Werner Randelshofer
 * @version $Id: AbstractTool.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public abstract class AbstractTool extends AbstractBean implements Tool {
    /**
     * This is set to true, if this is the active tool of the editor.
     */
    private boolean isActive;
    
    /**
     * This is set to true, while the tool is doing some work.
     * This prevents the currentView from being changed when a mouseEnter
     * event is received.
     */
    protected boolean isWorking;
    
    protected DrawingEditor editor;
    protected Point anchor = new Point();
    protected EventListenerList listenerList = new EventListenerList();
    private DrawingEditorProxy editorProxy;
    /*
    private PropertyChangeListener editorHandler;
    private PropertyChangeListener viewHandler;
     */
    
    /**
     * The input map of the tool.
     */
    private InputMap inputMap;
    /**
     * The action map of the tool.
     */
    private ActionMap actionMap;
    
    
    /** Creates a new instance. */
    public AbstractTool() {
        editorProxy = new DrawingEditorProxy();
        setInputMap(createInputMap());
        setActionMap(createActionMap());
    }
    
    public void addUndoableEditListener(UndoableEditListener l) {
        listenerList.add(UndoableEditListener.class, l);
    }
    
    public void removeUndoableEditListener(UndoableEditListener l) {
        listenerList.remove(UndoableEditListener.class, l);
    }
    
    public void activate(DrawingEditor editor) {
        this.editor = editor;
        editorProxy.setTarget(editor);
        isActive = true;
        
        // Repaint all handles
        for (DrawingView v : editor.getDrawingViews()) {
            v.repaintHandles();
        }
    }
    
    public void deactivate(DrawingEditor editor) {
        this.editor = editor;
        editorProxy.setTarget(null);
        isActive = false;
    }
    
    public boolean isActive() {
        return isActive;
    }
    
    protected DrawingView getView() {
        return editor.getActiveView();
    }
    protected DrawingEditor getEditor() {
        return editor;
    }
    protected Drawing getDrawing() {
        return getView().getDrawing();
    }
    protected Point2D.Double viewToDrawing(Point p) {
        return constrainPoint(getView().viewToDrawing(p));
    }
    protected Point2D.Double constrainPoint(Point p) {
        return constrainPoint(getView().viewToDrawing(p));
    }
    protected Point2D.Double constrainPoint(Point2D.Double p) {
        return getView().getConstrainer().constrainPoint(p);
    }
    
    /**
     * Sets the InputMap for the Tool.
     *
     * @see #keyPressed
     * @see #setActionMap
     */
    public void setInputMap(InputMap newValue) {
        inputMap = newValue;
    }
    /**
     * Gets the input map of the Tool
     */
    public InputMap getInputMap() {
        return inputMap;
    }
    /**
     * Sets the ActionMap for the Tool.
     * @see #keyPressed
     */
    public void setActionMap(ActionMap newValue) {
        actionMap = newValue;
    }
    /**
     * Gets the action map of the Tool
     */
    public ActionMap getActionMap() {
        return actionMap;
    }
    
    /**
     * Deletes the selection.
     * Depending on the tool, this could be selected figures, selected points
     * or selected text.
     */
    public void editDelete() {
        getView().getDrawing().removeAll(getView().getSelectedFigures());
    }
    /**
     * Cuts the selection into the clipboard.
     * Depending on the tool, this could be selected figures, selected points
     * or selected text.
     */
    public void editCut() {
    }
    /**
     * Copies the selection into the clipboard.
     * Depending on the tool, this could be selected figures, selected points
     * or selected text.
     */
    public void editCopy() {
    }
    /**
     * Duplicates the selection.
     * Depending on the tool, this could be selected figures, selected points
     * or selected text.
     */
    public void editDuplicate() {
    }
    /**
     * Pastes the contents of the clipboard.
     * Depending on the tool, this could be selected figures, selected points
     * or selected text.
     */
    public void editPaste() {
    }
    
    public void keyReleased(KeyEvent evt) {
        fireToolDone();
    }
    
    
    public void keyTyped(KeyEvent evt) {
    }
    
    /**
     * The Tool uses the InputMap to determine what to do, when a key is pressed.
     * If the corresponding value of the InputMap is a String, the ActionMap
     * of the tool is used, to find the action to be performed.
     * If the corresponding value of the InputMap is a ActionListener, the
     * actionPerformed method of the ActionListener is performed.
     */
    public void keyPressed(KeyEvent evt) {
        if (! evt.isConsumed()) {
            if (evt.getSource() instanceof Container) {
                editor.setActiveView(editor.findView((Container) evt.getSource()));
            }
            
            if (inputMap != null) {
                Object obj = inputMap.get(KeyStroke.getKeyStroke(evt.getKeyCode(),evt.getModifiers(), false));
                ActionListener al = null;
                if (obj instanceof ActionListener) {
                    al = (ActionListener) obj;
                } else if (obj != null && actionMap != null) {
                    al = actionMap.get(obj);
                }
                if (al != null) {
                    evt.consume();
                    al.actionPerformed(new ActionEvent(this, ActionEvent.ACTION_PERFORMED, "tool", evt.getWhen(), evt.getModifiers()));
                    fireToolDone();
                }
            }
        }
    }
    
    protected InputMap createInputMap() {
        InputMap m = new InputMap();
        
         m.put(KeyStroke.getKeyStroke(KeyEvent.VK_DELETE, 0), DeleteAction.ID);
         m.put(KeyStroke.getKeyStroke(KeyEvent.VK_BACK_SPACE, 0), DeleteAction.ID);
         m.put(KeyStroke.getKeyStroke(KeyEvent.VK_A, 0), SelectAllAction.ID);
         m.put(KeyStroke.getKeyStroke(KeyEvent.VK_A, InputEvent.CTRL_DOWN_MASK), SelectAllAction.ID);
         m.put(KeyStroke.getKeyStroke(KeyEvent.VK_A, InputEvent.META_DOWN_MASK), SelectAllAction.ID);
         m.put(KeyStroke.getKeyStroke(KeyEvent.VK_SPACE, 0), IncreaseHandleDetailLevelAction.ID);
         
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_LEFT, 0), MoveConstrainedAction.West.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_RIGHT, 0), MoveConstrainedAction.East.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_UP, 0), MoveConstrainedAction.North.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_DOWN, 0), MoveConstrainedAction.South.ID);
        
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_LEFT, InputEvent.ALT_DOWN_MASK), MoveAction.West.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_RIGHT, InputEvent.ALT_DOWN_MASK), MoveAction.East.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_UP, InputEvent.ALT_DOWN_MASK), MoveAction.North.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_DOWN, InputEvent.ALT_DOWN_MASK), MoveAction.South.ID);
        
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_LEFT, InputEvent.SHIFT_DOWN_MASK), MoveAction.West.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_RIGHT, InputEvent.SHIFT_DOWN_MASK), MoveAction.East.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_UP, InputEvent.SHIFT_DOWN_MASK), MoveAction.North.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_DOWN, InputEvent.SHIFT_DOWN_MASK), MoveAction.South.ID);
        
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_LEFT, InputEvent.CTRL_DOWN_MASK), MoveAction.West.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_RIGHT, InputEvent.CTRL_DOWN_MASK), MoveAction.East.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_UP, InputEvent.CTRL_DOWN_MASK), MoveAction.North.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_DOWN, InputEvent.CTRL_DOWN_MASK), MoveAction.South.ID);
        
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_C, InputEvent.CTRL_DOWN_MASK), CopyAction.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_C, InputEvent.META_DOWN_MASK), CopyAction.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_V, InputEvent.CTRL_DOWN_MASK), PasteAction.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_V, InputEvent.META_DOWN_MASK), PasteAction.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_X, InputEvent.CTRL_DOWN_MASK), CutAction.ID);
        m.put(KeyStroke.getKeyStroke(KeyEvent.VK_X, InputEvent.META_DOWN_MASK), CutAction.ID);
         
        
        return m;
    }
    protected ActionMap createActionMap() {
        ActionMap m = new ActionMap();
        
        m.put(DeleteAction.ID, new DeleteAction());
        m.put(SelectAllAction.ID, new SelectAllAction());
        m.put(IncreaseHandleDetailLevelAction.ID, new IncreaseHandleDetailLevelAction(editorProxy));
         
        m.put(MoveAction.East.ID, new MoveAction.East(editorProxy));
        m.put(MoveAction.West.ID, new MoveAction.West(editorProxy));
        m.put(MoveAction.North.ID, new MoveAction.North(editorProxy));
        m.put(MoveAction.South.ID, new MoveAction.South(editorProxy));
        m.put(MoveConstrainedAction.East.ID, new MoveConstrainedAction.East(editorProxy));
        m.put(MoveConstrainedAction.West.ID, new MoveConstrainedAction.West(editorProxy));
        m.put(MoveConstrainedAction.North.ID, new MoveConstrainedAction.North(editorProxy));
        m.put(MoveConstrainedAction.South.ID, new MoveConstrainedAction.South(editorProxy));
        
        m.put(CutAction.ID, new CutAction());
        m.put(CopyAction.ID, new CopyAction());
        m.put(PasteAction.ID, new PasteAction());
         
        return m;
    }
    
    public void mouseClicked(MouseEvent evt) {
    }
    
    
    public void mouseEntered(MouseEvent evt) {
        /*if (! isWorking) {
            editor.setActiveView(editor.findView((Container) evt.getSource()));
        }*/
    }
    
    public void mouseExited(MouseEvent evt) {
    }
    
    public void mouseMoved(MouseEvent evt) {
    }
    
    public void mousePressed(MouseEvent evt) {
        DrawingView view = editor.findView((Container) evt.getSource());
        view.requestFocus();
        anchor = new Point(evt.getX(), evt.getY());
        isWorking = true;
        fireToolStarted(view);
    }
    
    public void mouseReleased(MouseEvent evt) {
        isWorking = false;
    }
    
    public void addToolListener(ToolListener l) {
        listenerList.add(ToolListener.class, l);
    }
    
    public void removeToolListener(ToolListener l) {
        listenerList.remove(ToolListener.class, l);
    }
    
    /**
     *  Notify all listenerList that have registered interest for
     * notification on this event type.
     */
    protected void fireToolStarted(DrawingView view) {
        ToolEvent event = null;
        // Notify all listeners that have registered interest for
        // Guaranteed to return a non-null array
        Object[] listeners = listenerList.getListenerList();
        // Process the listeners last to first, notifying
        // those that are interested in this event
        for (int i = listeners.length-2; i>=0; i-=2) {
            if (listeners[i] == ToolListener.class) {
                // Lazily create the event:
                if (event == null)
                    event = new ToolEvent(this, view, new Rectangle(0,0,-1,-1));
                ((ToolListener)listeners[i+1]).toolStarted(event);
            }
        }
    }
    
    /**
     *  Notify all listenerList that have registered interest for
     * notification on this event type.
     */
    protected void fireToolDone() {
        ToolEvent event = null;
        // Notify all listeners that have registered interest for
        // Guaranteed to return a non-null array
        Object[] listeners = listenerList.getListenerList();
        // Process the listeners last to first, notifying
        // those that are interested in this event
        for (int i = listeners.length-2; i>=0; i-=2) {
            if (listeners[i] == ToolListener.class) {
                // Lazily create the event:
                if (event == null)
                    event = new ToolEvent(this, getView(), new Rectangle(0,0,-1,-1));
                ((ToolListener)listeners[i+1]).toolDone(event);
            }
        }
    }
    
    /**
     * Notify all listenerList that have registered interest for
     * notification on this event type.
     */
    protected void fireAreaInvalidated(Rectangle2D.Double r) {
        Point p1 = getView().drawingToView(new Point2D.Double(r.x, r.y));
        Point p2 = getView().drawingToView(new Point2D.Double(r.x+r.width, r.y+r.height));
        fireAreaInvalidated(
                new Rectangle(p1.x,p1.y,p2.x-p1.x,p2.y-p1.y)
                );
    }
    /**
     * Notify all listenerList that have registered interest for
     * notification on this event type.
     */
    protected void fireAreaInvalidated(Rectangle invalidatedArea) {
        ToolEvent event = null;
        // Notify all listeners that have registered interest for
        // Guaranteed to return a non-null array
        Object[] listeners = listenerList.getListenerList();
        // Process the listeners last to first, notifying
        // those that are interested in this event
        for (int i = listeners.length-2; i>=0; i-=2) {
            if (listeners[i] == ToolListener.class) {
                // Lazily create the event:
                if (event == null)
                    event = new ToolEvent(this, getView(), invalidatedArea);
                ((ToolListener)listeners[i+1]).areaInvalidated(event);
            }
        }
    }
    public void draw(Graphics2D g) {
    }
    
    public void updateCursor(DrawingView view, Point p) {
        if (view.isEnabled()) {
            Handle handle = view.findHandle(p);
            if (handle != null) {
                view.setCursor(handle.getCursor());
            } else {
                Figure figure = view.findFigure(p);
                Point2D.Double point = view.viewToDrawing(p);
                Drawing drawing = view.getDrawing();
                while (figure != null && ! figure.isSelectable()) {
                    figure = drawing.findFigureBehind(point, figure);
                }
                if (figure != null) {
                    view.setCursor(figure.getCursor(view.viewToDrawing(p)));
                } else {
                    view.setCursor(Cursor.getDefaultCursor());
                }
            }
        } else {
            view.setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));
        }
    }
    public String getToolTipText(DrawingView view, MouseEvent evt) {
        return null;
    }
    /**
     * Returns true, if this tool lets the user interact with handles.
     * <p>
     * Handles may draw differently, if interaction is not possible.
     * 
     * @return True, if this tool supports interaction with the handles.
     */
    public boolean supportsHandleInteraction() {
        return false;
    }
}
