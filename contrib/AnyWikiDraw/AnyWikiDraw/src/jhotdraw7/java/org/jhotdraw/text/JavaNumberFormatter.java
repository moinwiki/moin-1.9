/*
 * @(#)JavaNumberFormatter.java
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
 */
package org.jhotdraw.text;

import java.text.ParseException;
import javax.swing.JFormattedTextField.AbstractFormatterFactory;
import javax.swing.text.DefaultFormatter;
import javax.swing.text.DefaultFormatterFactory;

/**
 * {@code ScaledNumberFormatter} is used to format numbers written in the
 * Java programming syntax.
 *
 * @author Werner Randelshofer
 * @version $Id: JavaNumberFormatter.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class JavaNumberFormatter extends DefaultFormatter {

    /**
     * Specifies whether the formatter allows null values.
     */
    private double scaleFactor = 1d;
    private boolean allowsNullValue = false;
    private Comparable min;
    private Comparable max;
    private boolean appendsDotZero = true;

    /**
     * Creates a <code>NumberFormatter</code> with the a default
     * <code>NumberFormat</code> instance obtained from
     * <code>NumberFormat.getNumberInstance()</code>.
     */
    public JavaNumberFormatter() {
        super();
    }

    /**
     * Creates a NumberFormatter with the specified Format instance.
     */
    public JavaNumberFormatter(double min, double max, double scaleFactor) {
        this(min, max, scaleFactor, false, true);
    }

    /**
     * Creates a NumberFormatter with the specified Format instance.
     */
    public JavaNumberFormatter(double min, double max, double scaleFactor, boolean allowsNullValue, boolean appendsDotZero) {
        super();
        setMinimum(min);
        setMaximum(max);
        setScaleFactor(scaleFactor);
        setAllowsNullValue(allowsNullValue);
        setAppendsDotZero(appendsDotZero);
        setOverwriteMode(false);
    }

    /**
     * Sets the minimum permissible value. If the <code>valueClass</code> has
     * not been specified, and <code>minimum</code> is non null, the
     * <code>valueClass</code> will be set to that of the class of
     * <code>minimum</code>.
     *
     * @param minimum Minimum legal value that can be input
     * @see #setValueClass
     */
    public void setMinimum(Comparable minimum) {
        if (getValueClass() == null && minimum != null) {
            setValueClass(minimum.getClass());
        }
        min = minimum;
    }

    /**
     * Returns the minimum permissible value.
     *
     * @return Minimum legal value that can be input
     */
    public Comparable getMinimum() {
        return min;
    }

    /**
     * Sets the maximum permissible value. If the <code>valueClass</code> has
     * not been specified, and <code>max</code> is non null, the
     * <code>valueClass</code> will be set to that of the class of
     * <code>max</code>.
     *
     * @param max Maximum legal value that can be input
     * @see #setValueClass
     */
    public void setMaximum(Comparable max) {
        if (getValueClass() == null && max != null) {
            setValueClass(max.getClass());
        }
        this.max = max;
    }

    /**
     * Returns the maximum permissible value.
     *
     * @return Maximum legal value that can be input
     */
    public Comparable getMaximum() {
        return max;
    }

    /**
     * Changes the scale factor of the number formatter.
     *
     * @param newValue
     */
    public void setScaleFactor(double newValue) {
        scaleFactor = newValue;
    }

    /**
     * Returns the scale factor of the number formatter.
     */
    public double getScaleFactor() {
        return scaleFactor;
    }

    /**
     * Allows/Disallows null values.
     *
     * @param newValue
     */
    public void setAllowsNullValue(boolean newValue) {
        allowsNullValue = newValue;
    }

    /**
     * Returns true if null values are allowed.
     */
    public boolean getAllowsNullValue() {
        return allowsNullValue;
    }

    /**
     * Specifies whether ".0" is appended to double and float
     * values. By default this is true.
     *
     * @param newValue
     */
    public void setAppendsDotZero(boolean newValue) {
        appendsDotZero = newValue;
    }

    /**
     * Returns true if null values are allowed.
     */
    public boolean getAppendsDotZero() {
        return appendsDotZero;
    }

    /**
     * Returns a String representation of the Object <code>value</code>.
     * This invokes <code>format</code> on the current <code>Format</code>.
     *
     * @throws ParseException if there is an error in the conversion
     * @param value Value to convert
     * @return String representation of value
     */
    @Override
    public String valueToString(Object value) throws ParseException {
        if (value == null && allowsNullValue) {
            return "";
        }

        if (value instanceof Double) {
            double v = ((Double) value).doubleValue();
            v *= scaleFactor;
            String str = Double.toString(v);
            if (!appendsDotZero && str.endsWith(".0")) {
                str = str.substring(0, str.length() - 2);
            }
            return str;
        } else if (value instanceof Float) {
            float v = ((Float) value).floatValue();
            v = (float) (v * scaleFactor);
            String str = Float.toString(v);
            if (appendsDotZero && str.endsWith(".0")) {
                str = str.substring(0, str.length() - 2);
            }
            return str;
        } else if (value instanceof Long) {
            long v = ((Long) value).longValue();
            v = (long) (v * scaleFactor);
            return Long.toString(v);
        } else if (value instanceof Integer) {
            int v = ((Integer) value).intValue();
            v = (int) (v * scaleFactor);
            return Integer.toString(v);
        } else if (value instanceof Byte) {
            byte v = ((Byte) value).byteValue();
            v = (byte) (v * scaleFactor);
            return Byte.toString(v);
        } else if (value instanceof Short) {
            short v = ((Short) value).shortValue();
            v = (short) (v * scaleFactor);
            return Short.toString(v);
        }

        throw new ParseException("Value is of unsupported class " + value, 0);
    }

    /**
     * Returns the <code>Object</code> representation of the
     * <code>String</code> <code>text</code>.
     *
     * @param text <code>String</code> to convert
     * @return <code>Object</code> representation of text
     * @throws ParseException if there is an error in the conversion
     */
    @Override
    public Object stringToValue(String text) throws ParseException {
        if ((text == null || text.length() == 0) && getAllowsNullValue()) {
            return null;
        }
        Class valueClass = getValueClass();
        Object value;
        if (valueClass != null) {
            try {
                if (valueClass == Integer.class) {
                    int v = Integer.parseInt(text);
                    v = (int) (v / scaleFactor);
                    value = new Integer(v);
                } else if (valueClass == Long.class) {
                    long v = Long.parseLong(text);
                    v = (long) (v / scaleFactor);
                    value = new Long(v);
                } else if (valueClass == Float.class) {
                    float v = Float.parseFloat(text);
                    v = (float) (v / scaleFactor);
                    value = new Float(v);
                } else if (valueClass == Double.class) {
                    double v = Double.parseDouble(text);
                    v = (double) (v / scaleFactor);
                    value = new Double(v);
                } else if (valueClass == Byte.class) {
                    byte v = Byte.parseByte(text);
                    v = (byte) (v / scaleFactor);
                    value = new Byte(v);
                } else if (valueClass == Short.class) {
                    short v = Short.parseShort(text);
                    v = (short) (v / scaleFactor);
                    value = new Short(v);
                } else {
                    throw new ParseException("Unsupported value class " + valueClass, 0);
                }
            } catch (NumberFormatException e) {
                throw new ParseException(e.getMessage(), 0);
            }
        } else {
            throw new ParseException("Unsupported value class " + valueClass, 0);
        }

        try {
            if (!isValidValue(value, true)) {
                throw new ParseException("Value not within min/max range", 0);
            }
        } catch (ClassCastException cce) {
            throw new ParseException("Class cast exception comparing values: " + cce, 0);
        }
        return value;
    }

    /**
     * Returns true if <code>value</code> is between the min/max.
     *
     * @param wantsCCE If false, and a ClassCastException is thrown in
     *                 comparing the values, the exception is consumed and
     *                 false is returned.
     */
    @SuppressWarnings("unchecked")
    boolean isValidValue(Object value, boolean wantsCCE) {
        Comparable min = getMinimum();

        try {
            if (min != null && min.compareTo(value) > 0) {
                return false;
            }
        } catch (ClassCastException cce) {
            if (wantsCCE) {
                throw cce;
            }
            return false;
        }

        Comparable max = getMaximum();
        try {
            if (max != null && max.compareTo(value) < 0) {
                return false;
            }
        } catch (ClassCastException cce) {
            if (wantsCCE) {
                throw cce;
            }
            return false;
        }
        return true;
    }

    /**
     * Convenience method for creating a formatter factory with a
     * {@code ScalableNumberFormatter} and a Java-style DecimalFormat.
     * Doesn't allow null values and doesn't append ".0" to double and float values.
     */
    public static AbstractFormatterFactory createFormatterFactory(double min, double max, double scaleFactor) {
        return createFormatterFactory(min, max, scaleFactor, false, false);
    }

    /**
     * Convenience method for creating a formatter factory with a
     * {@code ScalableNumberFormatter} and a Java-style DecimalFormat.
     */
    public static AbstractFormatterFactory createFormatterFactory(double min, double max, double scaleFactor, boolean allowsNullValue, boolean appendsDotZero) {
        return new DefaultFormatterFactory(new JavaNumberFormatter(min, max, scaleFactor, allowsNullValue, appendsDotZero));
    }
}
