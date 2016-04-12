def octave_amplitudes(amplitudes, num_bins):

    bins = numpy.zeros(num_bins)
    i = 0
    ranges = bin_ranges(len(amplitudes), num_bins)
    for lower, upper in ranges: 

        if lower == upper:
            bin = amplitudes[lower]

        else: 
            #bin = amplitudes[lower:upper].mean()
            #bin = sum(amplitudes[lower:upper]) / float(len(amplitudes[lower:upper])) # average instead of mean
            #bin = numpy.max(amplitudes[lower:upper]) # this is an ugly hack instead of doing, like, statistical analysis or anything.
            bin = (numpy.max(amplitudes[lower:upper]) + numpy.mean(amplitudes[lower:upper])) / 2 # mean and max mixed

        if numpy.isnan(bin):
            bin = numpy.float64(0)

        bins[i] = bin
        i += 1

    return bins
