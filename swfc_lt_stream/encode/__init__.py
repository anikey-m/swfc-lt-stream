from swfc_lt_stream import sampler


class Encoder():
    def __init__(self, conf):
        self.conf = conf
        self.sampler = sampler.PRNG(conf.window, conf.c, conf.delta)
        self.sampler.set_seed(conf.seed)

    def run(self):
        pass
