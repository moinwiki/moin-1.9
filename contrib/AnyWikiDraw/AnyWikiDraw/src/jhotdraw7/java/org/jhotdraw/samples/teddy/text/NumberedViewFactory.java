/*
 * @(#)NumberedViewFactory.java
 *
 * Copyright (c) 2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and
 * contributors of the JHotDraw project ("the copyright holders").
 * You may not use, copy or modify this software, except in
 * accordance with the license agreement you entered into with
 * the copyright holders. For details see accompanying license terms.
 *
 * Original code (c) Stanislav Lapitsky
 * http://www.developer.com/java/other/article.php/3318421
 */

package org.jhotdraw.samples.teddy.text;

import javax.swing.text.*;
/**
 * NumberedViewFactory.
 *
 * @author Werner Randelshofer
 * @version $Id: NumberedViewFactory.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class NumberedViewFactory implements ViewFactory {
    private boolean isLineNumbersVisible;
    
    public void setLineNumbersVisible(boolean newValue) {
        boolean oldValue = isLineNumbersVisible;
        isLineNumbersVisible = newValue;
    }
    public boolean isLineNumbersVisible() {
        return isLineNumbersVisible;
    }
    
    public View create(Element elem) {
        String kind = elem.getName();
        if (kind != null)
            if (kind.equals(AbstractDocument.ContentElementName)) {
            return new LabelView(elem);
            } else if (kind.equals(AbstractDocument.
                ParagraphElementName)) {
           // if (isLineNumbersVisible()) {
                return new NumberedParagraphView(elem, this);
           // } else {
               // return new ParagraphView(elem);
            //}
            } else if (kind.equals(AbstractDocument.
                SectionElementName)) {
            return new BoxView(elem, View.Y_AXIS);
            } else if (kind.equals(StyleConstants.
                ComponentElementName)) {
            return new ComponentView(elem);
            } else if (kind.equals(StyleConstants.IconElementName)) {
            return new IconView(elem);
            }
        // default to text display
        return new LabelView(elem);
    }
}
