

def update_lambda(args, nn):
    temp = (args.lambda_ + args.phi * constraint(args, nn)).data.clone()
    if temp <= 0.:
        args.lambda_ = 0.
    else:
        args.lambda_ = temp