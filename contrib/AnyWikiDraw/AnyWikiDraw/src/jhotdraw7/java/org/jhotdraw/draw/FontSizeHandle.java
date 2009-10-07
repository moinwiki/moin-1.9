/*
 * @(#)FontSizeHandle.java
 *
 * Copyright (c) 1996-2008 by the original authors of JHotDraw
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

import java.util.Locale;
import javax.swing.undo.*;
import java.awt.*;
import java.awt.event.KeyEvent;
import java.awt.geom.*;
import org.jhotdraw.util.ResourceBundleUtil;
import static org.jhotdraw.draw.AttributeKeys.*;

/**
 * A {@link Handle} which can be used to change the font size of a
 * {@link TextHolderFigure}.
 *
 * @author Werner Randelshofer
 * @version $Id: FontSizeHandle.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class FontSizeHandle extends LocatorHandle {

    private float oldSize;
    private float newSize;
    private Object restoreData;

    /** Creates a new instance. */
    public FontSizeHandle(TextHolderFigure owner) {
        super(owner, new FontSizeLocator());
    }

    public FontSizeHandle(TextHolderFigure owner, Locator locator) {
        super(owner, locator);
    }

    /**
     * Draws this handle.
     */
    public void draw(Graphics2D g) {
        drawDiamond(g,
                (Color) getEditor().getHandleAttribute(HandleAttributeKeys.ATTRIBUTE_HANDLE_FILL_COLOR),
                (Color) getEditor().getHandleAttribute(HandleAttributeKeys.ATTRIBUTE_HANDLE_STROKE_COLOR));
    }

    public Cursor getCursor() {
        return Cursor.getPredefinedCursor(Cursor.S_RESIZE_CURSOR);
    }

    @Override
    protected Rectangle basicGetBounds() {
        Rectangle r = new Rectangle(getLocation());
        int h = getHandlesize();
        r.x -= h / 2;
        r.y -= h / 2;
        r.width = r.height = h;
        return r;
    }

    public void trackStart(Point anchor, int modifiersEx) {
        TextHolderFigure textOwner = (TextHolderFigure) getOwner();
        oldSize = newSize = textOwner.getFontSize();
        restoreData = textOwner.getAttributesRestoreData();
    }

    public void trackStep(Point anchor, Point lead, int modifiersEx) {
        TextHolderFigure textOwner = (TextHolderFigure) getOwner();

        Point2D.Double anchor2D = view.viewToDrawing(anchor);
        Point2D.Double lead2D = view.viewToDrawing(lead);
        if (TRANSFORM.get(textOwner) != null) {
            try {
                TRANSFORM.get(textOwner).inverseTransform(anchor2D, anchor2D);
                TRANSFORM.get(textOwner).inverseTransform(lead2D, lead2D);
            } catch (NoninvertibleTransformException ex) {
                ex.printStackTrace();
            }
        }
        newSize = (float) Math.max(1, oldSize + lead2D.y - anchor2D.y);
        textOwner.willChange();
        textOwner.setFontSize(newSize);
        textOwner.changed();
    }

    public void trackEnd(Point anchor, Point lead, int modifiersEx) {
        final TextHolderFigure textOwner = (TextHolderFigure) getOwner();
        final Object editRestoreData = restoreData;
        final float editNewSize = newSize;
        UndoableEdit edit = new AbstractUndoableEdit() {

            @Override
            public String getPresentationName() {
                ResourceBundleUtil labels =
                        ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
                return labels.getString("attribute.fontSize.text");
            }

            @Override
            public void undo() {
                super.undo();
                textOwner.willChange();
                textOwner.restoreAttributesTo(editRestoreData);
                textOwner.changed();
            }

            @Override
            public void redo() {
                super.redo();
                textOwner.willChange();
                textOwner.setFontSize(newSize);
                textOwner.changed();
            }
        };
        fireUndoableEditHappened(edit);
    }

    @Override
    public void keyPressed(KeyEvent evt) {
        final TextHolderFigure textOwner = (TextHolderFigure) getOwner();
        oldSize = newSize = textOwner.getFontSize();

        switch (evt.getKeyCode()) {
            case KeyEvent.VK_UP:
                if (newSize > 1) {
                    newSize -= 1f;
                }
                evt.consume();
                break;
            case KeyEvent.VK_DOWN:
                newSize++;
                evt.consume();
                break;
            case KeyEvent.VK_LEFT:
                evt.consume();
                break;
            case KeyEvent.VK_RIGHT:
                evt.consume();
                break;
        }
        if (newSize != oldSize) {
        restoreData = textOwner.getAttributesRestoreData();
        textOwner.willChange();
        textOwner.setFontSize(newSize);
        textOwner.changed();
            final Object editRestoreData = restoreData;
            final float editNewSize = newSize;
            UndoableEdit edit = new AbstractUndoableEdit() {

                @Override
                public String getPresentationName() {
                    ResourceBundleUtil labels =
                            ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
                    return labels.getString("attribute.fontSize");
                }

                @Override
                public void undo() {
                    super.undo();
                    textOwner.willChange();
                    textOwner.restoreAttributesTo(editRestoreData);
                    textOwner.changed();
                }

                @Override
                public void redo() {
                    super.redo();
                    textOwner.willChange();
                    textOwner.setFontSize(newSize);
                    textOwner.changed();
                }
            };
            fireUndoableEditHappened(edit);
        }
    }

    @Override
    public String getToolTipText(Point p) {
        return ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels").getString("handle.fontSize.toolTipText");
    }
}
