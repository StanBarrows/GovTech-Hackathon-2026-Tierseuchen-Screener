<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('events', function (Blueprint $table) {
            $table->id();

            $table->string('disease');
            $table->string('subtype')->nullable();
            $table->string('species')->nullable();
            $table->string('population')->nullable();
            $table->string('source');

            $table->string('external_id')->nullable()->index();
            $table->timestamp('occurred_at')->index();

            $table->string('admin_level_1')->nullable()->index();
            $table->string('admin_level_2')->nullable();
            $table->string('admin_level_3')->nullable();

            $table->decimal('latitude', 9, 6)->nullable();
            $table->decimal('longitude', 9, 6)->nullable();

            $table->unsignedInteger('cases')->nullable();
            $table->unsignedInteger('deaths')->nullable();
            $table->unsignedInteger('susceptible')->nullable();

            $table->decimal('distance_km', 8, 2)->nullable();
            $table->decimal('relevance_score', 5, 2)->nullable();
            $table->unsignedTinyInteger('priority')->nullable();

            $table->timestamps();

            $table->index(['latitude', 'longitude']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('events');
    }
};
