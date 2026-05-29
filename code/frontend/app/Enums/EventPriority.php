<?php

namespace App\Enums;

enum EventPriority: int
{
    case Low = 1;
    case Medium = 2;
    case High = 3;
    case Critical = 4;
}
